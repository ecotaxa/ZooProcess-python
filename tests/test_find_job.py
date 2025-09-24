import pytest

from modern.tasks import JobScheduler, Job


# Define a mock job class for testing
class FakeTestJob(Job):
    def __init__(self, param1, param2):
        super().__init__((param1, param2))
        self.param1 = param1
        self.param2 = param2

    def prepare(self):
        pass

    def run(self):
        pass


# Define another mock job class for testing different class types
class AnotherTestJob(Job):
    def __init__(self, param1, param2):
        super().__init__((param1, param2))
        self.param1 = param1
        self.param2 = param2

    def prepare(self):
        pass

    def run(self):
        pass


@pytest.fixture
def clear_jobs():
    # Clear the jobs list before each test
    with JobScheduler.jobs_lock:
        JobScheduler._jobs.clear()
    yield


def test_find_job_same_class_and_params(clear_jobs):
    # Create a job
    job1 = FakeTestJob(param1="value1", param2="value2")

    # Submit the job to the scheduler
    JobScheduler.submit(job1)

    # Create another job with the same parameters
    job2 = FakeTestJob(param1="value1", param2="value2")

    # Find the job using the find_job method
    found_job = JobScheduler.find_jobs_like(job2, Job.will_do)

    # Assert that the found job is the same as the submitted job
    assert len(found_job) == 1
    assert found_job[0].job_id == job1.job_id


def test_find_job_different_params(clear_jobs):
    # Create a job
    job1 = FakeTestJob(param1="value1", param2="value2")

    # Submit the job to the scheduler
    JobScheduler.submit(job1)

    # Create another job with different parameters
    job2 = FakeTestJob(param1="value1", param2="different_value")

    # Find the job using the find_job method
    found_job = JobScheduler.find_jobs_like(job2, Job.will_do)

    # Assert that no job is found
    assert len(found_job) == 0


def test_find_job_different_class(clear_jobs):
    # Create a job
    job1 = FakeTestJob(param1="value1", param2="value2")

    # Submit the job to the scheduler
    JobScheduler.submit(job1)

    # Create a job of a different class
    job2 = AnotherTestJob(param1="value1", param2="value2")

    # Find the job using the find_job method
    found_job = JobScheduler.find_jobs_like(job2, Job.will_do)

    # Assert that no job is found
    assert len(found_job) == 0
