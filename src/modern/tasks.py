# EcoTaxa-inspired background work handling
# This file is part of Ecotaxa, see license.md in the application root directory for license informations.
# Copyright (C) 2015-2021  Picheral, Colin, Irisson (UPMC-CNRS)
#
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from logging import Logger
from pathlib import Path
from threading import Thread, Event
from typing import Any, Optional, Tuple, List, Callable

from helpers.logger import logger, logs_dir, NullLogger

# Typings, to be clear that these are not e.g. task IDs
JobIDT = int

# Concurrency cap (configurable through env)
MAX_CONCURRENCY: int = int(os.getenv("JOB_MAX_CONCURRENCY", "4"))


class JobStateEnum(str, Enum):
    Pending = "P"  # Waiting for an execution thread
    Running = "R"  # Being executed inside a thread
    Error = "E"  # Stopped with error
    Finished = "F"  # Done


class Job(ABC):
    # Common Job traits
    def __init__(self, params: Tuple):
        self.params = params
        self.job_id = 0
        self.state: JobStateEnum = JobStateEnum.Pending
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.last_log_line = None
        self.logger: Logger = NullLogger()

    def _setup_job_logger(self, log_file: Optional[Path] = None) -> Logger:
        """
        Set up a logger for this job that writes to a file named after the job_id.
        """
        # Create a logger with the job_id as part of the name
        logger_name = f"job_{self.job_id}"
        job_logger = logging.getLogger(logger_name)
        job_logger.setLevel(logging.DEBUG)

        # Create file formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create a file handler with a filename based on job_id
        if log_file is None:
            log_file = logs_dir / f"job_{self.job_id}.log"
        # Use mode='w' to clear the log file at job startup
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Create a custom handler to store the last log line
        class LastLogHandler(logging.Handler):
            def __init__(self, job):
                super().__init__()
                self.job = job

            def emit(self, record):
                self.job.last_log_line = self.format(record)

        # Create eye formatter, users will see this output
        eye_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M"
        )
        last_log_handler = LastLogHandler(self)
        last_log_handler.setLevel(logging.INFO)
        last_log_handler.setFormatter(eye_formatter)

        # Add handlers to logger
        job_logger.addHandler(file_handler)
        job_logger.addHandler(last_log_handler)

        return job_logger

    @abstractmethod
    def prepare(self):
        """
        Start the job execution. This method must be implemented by subclasses.
        It's supposed to prepare prerequisites (fast) and raise in case of a problem.
        """

    @abstractmethod
    def run(self):
        """
        Run the job execution. This method must be implemented by subclasses.
        """

    def mark_started(self):
        """
        Utility for subclasses to mark job execution as started.
        """
        self.state = JobStateEnum.Running
        self.updated_at = datetime.now()
        self.logger.info(f"Job {self.job_id} started")

    def mark_alive(self):
        """
        Update the job's updated_at timestamp to indicate it's still active.
        """
        self.updated_at = datetime.now()
        self.logger.debug(f"Job {self.job_id} marked as alive at {self.updated_at}")

    def mark_done(self, logger: Logger):
        """
        Signal the end of running the job.
        """
        self.updated_at = datetime.now()
        self.logger.debug(f"Job {self.job_id} finished at {self.updated_at}")
        logger.info(f"Job {self.job_id} finished at {self.updated_at}")

    def is_done(self) -> bool:
        return self.state in (JobStateEnum.Finished, JobStateEnum.Error)

    def will_do(self) -> bool:
        return self.state in (JobStateEnum.Pending, JobStateEnum.Running)

    def is_in_error(self) -> bool:
        return self.state in (JobStateEnum.Error,)


class JobRunner(Thread):
    """
    Run a job in a dedicated thread
    """

    def __init__(self, a_job: Job):
        super().__init__(name="Job #%d" % a_job.job_id)
        self.job = a_job

    def run(self) -> None:
        job = self.job
        try:
            job.mark_started()
            job.prepare()
        except Exception as te:
            self.tech_error(te)
            return
        try:
            job.run()
            job.logger.info("Processing completed successfully")
            job.state = JobStateEnum.Finished
            job.mark_done(logger)
        except Exception as e:
            job.logger.error(f"Error during processing: {str(e)}", exc_info=True)
            job.state = JobStateEnum.Error
            job.mark_done(logger)
            raise

    def tech_error(self, te: Any) -> None:
        """
        Technical problem, which cannot be managed by the service
        as it was not possible to start it. Report here.
        """
        self.job.state = JobStateEnum.Error
        self.job.logger.error(f"Failed to start due to: {str(te)}")
        self.job.mark_done(logger)


class JobScheduler:
    """
    In charge of launching/monitoring subprocesses i.e. keep sync b/w processes and their images in memory.
    These are not really processes, just threads, so far.
    """

    # Track multiple concurrent runners
    active_runners: set[JobRunner] = set()  # Only written by JobTimer_s_

    the_timer: Optional[threading.Timer] = (
        None  # First creation by Main, replacements by JobTimer_s_
    )
    do_run: Event = Event()  # R/W by Main & JobTimer

    # Counter for generating unique job IDs
    _next_id: int = 1
    # In-memory storage for jobs
    _jobs: list[Job] = []
    # Mutex for _jobs access (also protects active_runners)
    jobs_lock: threading.RLock = threading.RLock()

    @classmethod
    def _prune_finished(cls) -> None:
        """Remove completed/terminated runners from the active set."""
        with cls.jobs_lock:
            dead = {r for r in cls.active_runners if not r.is_alive()}
            if dead:
                for r in dead:
                    try:
                        r.join(timeout=0)
                    except Exception:
                        pass
                cls.active_runners.difference_update(dead)

    @classmethod
    def _pick_a_pending(cls) -> Optional[Job]:
        """Pick a single pending job and mark it Running under the lock.
        Returns the job if found, otherwise None.
        """
        with cls.jobs_lock:
            for job in cls._jobs:
                if job.state == JobStateEnum.Pending:
                    job.state = JobStateEnum.Running
                    return job
        return None

    @classmethod
    def _run_one(cls) -> None:
        """
        Fill available concurrency slots with pending jobs.
        Current thread: JobTimer
        """
        # 1) Remove completed runners
        cls._prune_finished()

        # 2) How many new jobs can we start?
        with cls.jobs_lock:
            running_count = len(cls.active_runners)
            free_slots = max(MAX_CONCURRENCY - running_count, 0)

        if free_slots <= 0:
            return

        # 3) Start at most one pending job per tick (queue will fill others)
        job = cls._pick_a_pending()
        if job is not None:
            logger.info("Found job to run: %s", str(job))
            runner = JobRunner(job)
            runner.start()
            with cls.jobs_lock:
                cls.active_runners.add(runner)

    @classmethod
    def launch_at_interval(cls, interval: int) -> None:
        """
        Launch a job if possible, then wait a bit before accessing the next one.
        Current thread: Main for the first launch, JobTimer (_different ones_) for others
        """
        cls.do_run.set()
        cls._create_and_launch_timer(interval)

    @classmethod
    def _create_and_launch_timer(cls, interval: int) -> None:
        cls.the_timer = threading.Timer(
            interval=interval, function=cls.launch, args=[interval]
        )
        cls.the_timer.name = "JobTimer"
        cls.the_timer.start()

    @classmethod
    def launch(cls, interval: int) -> None:
        # Current thread: JobTimer_s_
        try:
            # noinspection PyProtectedMember
            cls._run_one()
        except Exception as e:
            logger.exception("Job run() exception: %s", e)
        if not cls.do_run.is_set():
            # Join all active runners before stopping
            with cls.jobs_lock:
                runners = list(cls.active_runners)
            for r in runners:
                try:
                    r.join()
                except Exception:
                    pass
            with cls.jobs_lock:
                cls.active_runners.clear()
            cls.the_timer = None
        else:
            cls._create_and_launch_timer(interval)

    @classmethod
    def shutdown(cls) -> None:
        """
        Clean close of multi-threading resources: Runner, Timer and Event
        Restore class-loading time state.
        Current thread: Main
        """
        if cls.do_run.is_set():
            # Signal the timer to stop and cancel itself
            cls.do_run.clear()
            # Wait for it gone
            while cls.the_timer is not None:
                time.sleep(1)

    @classmethod
    def get_new_id(cls) -> int:
        """
        Returns a unique incremented ID using a class variable.
        """
        job_id = cls._next_id
        cls._next_id += 1
        return job_id

    @classmethod
    def get_job(cls, job_id: int) -> Optional[Job]:
        """
        Get a job by its ID.

        Args:
            job_id: The ID of the job to retrieve.

        Returns:
            The job with the specified ID, or None if no job with that ID is found.
        """
        with cls.jobs_lock:
            for job in cls._jobs:
                if job.job_id == job_id:
                    return job
        return None

    @classmethod
    def submit(cls, task: Job):
        """
        Submit a job to be executed by the scheduler.
        The job will be added to the in-memory storage and executed when
        a runner is available.
        """
        # Ensure the job has a unique ID
        if task.job_id <= 0:
            task.job_id = cls.get_new_id()
        # Ensure the job state is Pending
        task.state = JobStateEnum.Pending
        # Add the job to the in-memory storage
        with cls.jobs_lock:
            cls._jobs.append(task)
        logger.info(f"Job #{task.job_id} submitted")

    @classmethod
    def find_jobs_like(cls, task: Job, state_def: Callable[[Job], bool]) -> List[Job]:
        """
        Find jobs matching exactly the class and params of the provided job, and able
        to complete the task.

        Args:
            task: The job to match.
            state_def: a function to filter jobs.

        Returns:
            All jobs matching the class and parameters of the provided job.
        """
        with cls.jobs_lock:
            ret = []
            for job in cls._jobs:
                # Check if the job is of the same class type
                if not isinstance(job, type(task)):
                    continue
                if job.params == task.params:
                    if state_def(job):
                        ret.append(job)
            return sorted(ret, key=lambda a_job: a_job.created_at, reverse=True)
