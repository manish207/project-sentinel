from project_sentinel.domain.task import Task
from dataclasses import dataclass


@dataclass
class EisenhowerMatrix:
    do: list[Task]
    schedule: list[Task]
    delegate: list[Task]
    eliminate: list[Task]
