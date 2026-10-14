import json
import io
import csv
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict, deque
from sqlalchemy.orm import Session
from app.db.models import MissionTask
from app.schemas.mission_plan import MissionTaskCreate, MissionTaskUpdate, MissionTaskResponse, ScheduleGenerateResponse

class MissionPlanningService:
    @staticmethod
    def get_tasks(db: Session) -> List[MissionTask]:
        return db.query(MissionTask).all()

    @staticmethod
    def get_task(db: Session, task_id: str) -> Optional[MissionTask]:
        return db.query(MissionTask).filter(MissionTask.id == task_id).first()

    @staticmethod
    def create_task(db: Session, task_in: MissionTaskCreate) -> MissionTask:
        existing = db.query(MissionTask).filter(MissionTask.id == task_in.id).first()
        if existing:
            raise ValueError(f"Task with ID '{task_in.id}' already exists.")

        task = MissionTask(
            id=task_in.id,
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            duration_minutes=task_in.duration_minutes,
            earliest_start_minutes=task_in.earliest_start_minutes,
            deadline_minutes=task_in.deadline_minutes,
            dependencies_json=json.dumps(task_in.dependencies),
            resources_json=json.dumps(task_in.resources or {}),
            status="UNSCHEDULED",
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, task_id: str, task_in: MissionTaskUpdate) -> MissionTask:
        task = db.query(MissionTask).filter(MissionTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        if task_in.title is not None:
            task.title = task_in.title
        if task_in.description is not None:
            task.description = task_in.description
        if task_in.priority is not None:
            task.priority = task_in.priority
        if task_in.duration_minutes is not None:
            task.duration_minutes = task_in.duration_minutes
        if task_in.earliest_start_minutes is not None:
            task.earliest_start_minutes = task_in.earliest_start_minutes
        if task_in.deadline_minutes is not None:
            task.deadline_minutes = task_in.deadline_minutes
        if task_in.dependencies is not None:
            task.dependencies_json = json.dumps(task_in.dependencies)
        if task_in.resources is not None:
            task.resources_json = json.dumps(task_in.resources)
        if task_in.status is not None:
            task.status = task_in.status

        # Reset schedule upon task modification
        task.status = "UNSCHEDULED"
        task.scheduled_start_minutes = None
        task.scheduled_end_minutes = None
        task.scheduling_notes = "Pending replan"

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: str) -> None:
        task = db.query(MissionTask).filter(MissionTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")
        db.delete(task)
        db.commit()

    @staticmethod
    def detect_cycles(tasks: List[MissionTask]) -> List[List[str]]:
        """
        Detect circular dependencies in task DAG using Tarjan's or DFS cycle detection.
        Returns list of cycles found (e.g. [['TSK-1', 'TSK-2', 'TSK-1']]).
        """
        adj = defaultdict(list)
        task_ids = {t.id for t in tasks}

        for t in tasks:
            deps = json.loads(t.dependencies_json) if t.dependencies_json else []
            for d in deps:
                if d in task_ids:
                    adj[d].append(t.id)

        cycles = []
        visited = {}  # 0=unvisited, 1=visiting, 2=visited
        parent_map = {}

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            for neighbor in adj[node]:
                if visited.get(neighbor, 0) == 1:
                    # Cycle detected
                    idx = path.index(neighbor) if neighbor in path else 0
                    cycles.append(path[idx:] + [neighbor])
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path + [neighbor])
            visited[node] = 2

        for t in tasks:
            if visited.get(t.id, 0) == 0:
                dfs(t.id, [t.id])

        return cycles

    @staticmethod
    def generate_schedule(db: Session) -> ScheduleGenerateResponse:
        """
        Documented Scheduling Heuristic:
        Topological precedence sort + Priority & Earliest Deadline First (EDF).
        Respects:
        1. Dependency finish-to-start constraints: start_i >= max(end_deps)
        2. Earliest start time: start_i >= earliest_start
        3. Single instrument / link resource constraint (simulated serial payload channel)
        """
        tasks = db.query(MissionTask).all()
        if not tasks:
            return ScheduleGenerateResponse(
                success=True,
                total_tasks=0,
                scheduled_tasks=0,
                unscheduled_tasks=0,
                conflicts=[],
                makespan_minutes=0,
                tasks=[],
            )

        # 1. Detect cycles
        cycles = MissionPlanningService.detect_cycles(tasks)
        if cycles:
            cycle_desc = [" -> ".join(c) for c in cycles]
            for t in tasks:
                t.status = "BLOCKED"
                t.scheduling_notes = f"Blocked by dependency cycle: {cycle_desc[0]}"
            db.commit()
            return ScheduleGenerateResponse(
                success=False,
                total_tasks=len(tasks),
                scheduled_tasks=0,
                unscheduled_tasks=len(tasks),
                conflicts=[f"Dependency cycle detected: {c}" for c in cycle_desc],
                makespan_minutes=0,
                tasks=[MissionPlanningService._to_response(t) for t in tasks],
            )

        # 2. Build DAG in-degree
        task_map = {t.id: t for t in tasks}
        in_degree = {t.id: 0 for t in tasks}
        adj = defaultdict(list)
        missing_dep_conflicts = []

        for t in tasks:
            deps = json.loads(t.dependencies_json) if t.dependencies_json else []
            for d in deps:
                if d not in task_map:
                    missing_dep_conflicts.append(f"Task '{t.id}' depends on non-existent task '{d}'")
                else:
                    adj[d].append(t.id)
                    in_degree[t.id] += 1

        if missing_dep_conflicts:
            for t in tasks:
                t.status = "BLOCKED"
                t.scheduling_notes = "Missing required dependency"
            db.commit()
            return ScheduleGenerateResponse(
                success=False,
                total_tasks=len(tasks),
                scheduled_tasks=0,
                unscheduled_tasks=len(tasks),
                conflicts=missing_dep_conflicts,
                makespan_minutes=0,
                tasks=[MissionPlanningService._to_response(t) for t in tasks],
            )

        # Ready queue: tasks with in_degree == 0
        ready = [t for t in tasks if in_degree[t.id] == 0]
        # Sort ready by priority asc (1 is highest), then deadline asc (EDF)
        def sort_key(task: MissionTask):
            deadline = task.deadline_minutes if task.deadline_minutes is not None else 999999
            return (task.priority, deadline, task.earliest_start_minutes)

        scheduled_ends: Dict[str, int] = {}
        conflicts: List[str] = []
        scheduled_count = 0
        current_timeline_pointer = 0

        while ready:
            ready.sort(key=sort_key)
            task = ready.pop(0)

            deps = json.loads(task.dependencies_json) if task.dependencies_json else []
            earliest_dep_finish = max([scheduled_ends.get(d, 0) for d in deps], default=0)

            proposed_start = max(task.earliest_start_minutes, earliest_dep_finish, current_timeline_pointer)
            proposed_end = proposed_start + task.duration_minutes

            # Check deadline constraint
            if task.deadline_minutes is not None and proposed_end > task.deadline_minutes:
                conflicts.append(
                    f"Deadline violation: Task '{task.id}' ({task.title}) completes at T+{proposed_end}m, exceeding deadline T+{task.deadline_minutes}m."
                )
                task.status = "BLOCKED"
                task.scheduled_start_minutes = proposed_start
                task.scheduled_end_minutes = proposed_end
                task.scheduling_notes = f"Exceeds deadline T+{task.deadline_minutes}m."
            else:
                task.status = "SCHEDULED"
                task.scheduled_start_minutes = proposed_start
                task.scheduled_end_minutes = proposed_end
                task.scheduling_notes = f"Scheduled nominally at T+{proposed_start}m to T+{proposed_end}m."
                scheduled_count += 1
                current_timeline_pointer = proposed_end

            scheduled_ends[task.id] = proposed_end

            # Decrement in_degree for successors
            for nxt_id in adj[task.id]:
                in_degree[nxt_id] -= 1
                if in_degree[nxt_id] == 0:
                    ready.append(task_map[nxt_id])

        db.commit()

        makespan = max(scheduled_ends.values()) if scheduled_ends else 0
        return ScheduleGenerateResponse(
            success=len(conflicts) == 0,
            total_tasks=len(tasks),
            scheduled_tasks=scheduled_count,
            unscheduled_tasks=len(tasks) - scheduled_count,
            conflicts=conflicts,
            makespan_minutes=makespan,
            tasks=[MissionPlanningService._to_response(t) for t in tasks],
        )

    @staticmethod
    def _to_response(t: MissionTask) -> MissionTaskResponse:
        return MissionTaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            priority=t.priority,
            duration_minutes=t.duration_minutes,
            earliest_start_minutes=t.earliest_start_minutes,
            deadline_minutes=t.deadline_minutes,
            dependencies=json.loads(t.dependencies_json) if t.dependencies_json else [],
            resources=json.loads(t.resources_json) if t.resources_json else None,
            status=t.status,
            scheduled_start_minutes=t.scheduled_start_minutes,
            scheduled_end_minutes=t.scheduled_end_minutes,
            scheduling_notes=t.scheduling_notes,
        )
