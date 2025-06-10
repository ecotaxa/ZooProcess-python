# Process a scan from its background until segmentation
from ZooProcess_lib.ZooscanFolder import ZooscanProjectFolder
from modern.tasks import Job, JobStateEnum


class BackgroundAndScanToSegmented(Job):

    def __init__(
        self, zoo_project: ZooscanProjectFolder, sample_name: str, subsample_name: str
    ):
        super().__init__()
        self.zoo_project = zoo_project
        self.sample_name = sample_name
        self.subsample_name = subsample_name

    def start(self):
        """
        Start the job execution.
        Process a scan from its background until segmentation.
        """
        # Mark the job as started
        self.mark_started()

        # Log the start of the job execution
        self.logger.info(
            f"Starting processing for project: {self.zoo_project.name}, sample: {self.sample_name}, subsample: {self.subsample_name}"
        )

        try:
            # Implementation of the job execution would go here
            self.logger.info("Processing completed successfully")
            self.state = JobStateEnum.Finished
            self.mark_alive()
        except Exception as e:
            self.logger.error(f"Error during processing: {str(e)}", exc_info=True)
            self.state = JobStateEnum.Error
            self.mark_alive()
            raise
