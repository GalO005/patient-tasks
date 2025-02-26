from collections.abc import Iterable
from tinydb import Query, where
from models.patient_task import PatientTask
from models.patient_request import PatientRequest
import db.db_tinydb as db

from operator import attrgetter

task_date_getter = attrgetter('updated_date')

Task = Query()


class TaskService:

    def updates_tasks(self, tasks: list[PatientTask]):
        # Question : This code is the result of a limitation by TinyDB. What is the issue and what feature
        # would a more complete DB solution offer ?
        # Answer: The main limitations and missing features are:
        # 1. Bulk Operations: TinyDB doesn't support bulk upserts, forcing us to loop through tasks
        #    and perform individual upserts. A more complete DB (like MongoDB) would support
        #    bulk operations like bulkWrite() or insertMany() with upsert option.
        # 2. Transactions: TinyDB doesn't support ACID transactions. If the system crashes mid-update,
        #    we could end up with inconsistent state. Production DBs would offer transaction support
        #    to ensure all updates succeed or all fail.
        # 3. Indexes: TinyDB has limited indexing support. Production DBs would allow creating indexes
        #    on frequently queried fields (like status, patient_id) for better performance.
        # 4. Atomic Operations: No support for atomic operations like findAndModify. Each upsert
        #    requires a separate read and write operation.
        for task in tasks:
            db.tasks.upsert(task.model_dump(), Task.id == task.id)

    def get_open_tasks(self) -> Iterable[PatientTask]:
        return (PatientTask(**task_doc) for task_doc in db.tasks.search(where("status") == 'Open'))
