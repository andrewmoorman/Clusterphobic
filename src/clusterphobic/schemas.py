'''
Module Docstring
'''
import datetime
from uuid import uuid4
from typing import Optional
from pathlib import Path
from typing_extensions import Annotated
from pydantic import BaseModel, PositiveInt, Field, BeforeValidator
from pydantic import field_validator, model_validator
from clusterphobic import enums


class JobParametersSchema(BaseModel):
    '''
    A Pydantic schema/model to capture all job parameters/options supplied to
    the job scheduler when submitting a job.
    For optional parameters, practice is to supply nothing and rely on default
    values set by the scheduler, itself.
    '''
    ### Pydantic Fields
    # Required fields
    n_cores: PositiveInt = Field(
        ge=1,
        description="Number of CPU cores.",
    )
    mem_per_core: PositiveInt = Field(
        ge=1,
        description="Minimum memory required per allocated CPU.",
    )
    # Optional fields
    # NOTE: Job name is optional for user, but required by scheduler
    job_name: Optional[str] = Field(
        default_factory=lambda: uuid4().hex,
        min_length=1,
        max_length=100,
        description="Name for your job.",
    )
    n_cores_per_node: Optional[PositiveInt] = Field(
        default=None,
        ge=1,
        description="Number of CPU cores per node."
    )
    run_time: Optional[datetime.time] = Field(
        default=None,
        description="Limit on the total run time of the job.",
    )
    n_gpus: Optional[PositiveInt] = Field(
        default=None,
        ge=1,
        description="Number of GPUs."
    )
    mem_per_gpu: Optional[PositiveInt] = Field(
        default=None,
        ge=1,
        description="Minimum memory required per allocated GPU."
    )

    ### Validators and formatting functions
    @staticmethod
    @field_validator("run_time", mode="before")
    def zfill_time(time):
        ''' Fix time fields in string format '''
        if isinstance(time, str):
            return ':'.join(map(lambda t: t.zfill(2), time.split(':')))
        return time


class SubmissionSchema(BaseModel):
    '''
    A Pydantic schema/model to represent a job request submitted to the 
    scheduler. Users can supply a command or job script (shell) to run, or 
    launch an interactive job.
    '''
    ### Pydantic fields
    # Required fields
    scheduler: Annotated[
        enums.Scheduler,
        BeforeValidator(str.lower),
        Field(
            description="Job scheduling system to use.",
            examples=[s.name for s in enums.Scheduler],
        ),
    ]
    job_parameters: JobParametersSchema
    # Optional fields
    interactive: Optional[bool] = Field(
        default=None,  # NOTE: explicitly None, not False, for validation
        description=(
            "Whether to launch an interactive job (e.g., as opposed to a "
            "batch submission)."
        ),
    )
    command: Optional[str] = Field(
        default=None,
        description="Simple command (string) to submit."
    )
    script: Optional[Path] = Field(
        default=None,
        description="Shell script (file) to submit for processing."
    )

    # Validators and formatting functions
    @model_validator(mode='after')
    def validate_xor(self):
        '''
        Ensure only one submission type is used (i.e., command, shell script,
        or interactive are mutually exclusive)
        '''
        check_fields = [self.command, self.script, self.interactive]
        ct = sum(map(lambda x: x is not None, check_fields))
        msg = (
            "Received insufficient or contradictory submission types. Please "
            "supply exactly one of 'command', 'script', or 'interactive'."
        )
        assert ct == 1, msg
