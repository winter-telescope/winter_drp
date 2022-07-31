from winterdrp.pipelines import get_pipeline
from winterdrp.errors import ErrorStack
from winterdrp.utils.send_email import send_gmail
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Watchdog:

    def __init__(
            self,
            night: str,
            pipeline: str,
            configuration: str = None,
            email_sender: str = None,
            email_recipients: str | list = None,
    ):
        self.night = night
        self.pipeline_name = pipeline
        self.pipeline = get_pipeline(pipeline, configuration=configuration)

        check_email = np.sum([x is None for x in [email_recipients, email_sender]])
        if np.sum(check_email) == 1:
            err = "In order to send emails, you must specify both a a sender and a recipient. \n" \
                  f"In this case, sender is {email_sender} and recipent is {email_recipients}."
            logger.error(err)
            raise ValueError(err)

        if np.sum(check_email) == 2:
            self.email_info = (email_sender, email_recipients)
        else:
            self.email_info = None

    def summarise_errors(self, errorstack: ErrorStack):

        summary = errorstack.summarise_error_stack()

        if self.email_info is not None:

            sender, recipients = self.email_info

            subject = f"{self.pipeline_name}: Summary for night {self.night}"

            send_gmail(
                email_sender=sender,
                email_recipients=recipients,
                email_subject=subject,
                email_text=summary
            )

    def process_images(self):
        pass

    def process_night(self):
        batches, errorstack = self.pipeline.reduce_images([])
        self.summarise_errors(errorstack=errorstack)


if __name__ == "__main__":
    watchdog = Watchdog(
        pipeline="summer",
        email_sender="winter.data.reduction.password@gmail.com",
        email_recipients=["rdstein@caltech.edu"]
    )

