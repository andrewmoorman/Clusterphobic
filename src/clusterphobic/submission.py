'''
Module docstring
'''
from subprocess import run
from clusterphobic.schemas import SubmissionSchema
from clusterphobic.template import get_template
import shlex


class Submission(SubmissionSchema):
    '''
    Class docstring
    '''
    def render_submission(self):
        ''' Render this job submission command '''
        template = get_template(f'{self.scheduler}_submission.txt')
        return template.render(submission=self)

    def submit_job(self):
        ''' Submit this job submission through terminal '''
        cmd_str = self.render_submission()
        cmd = [i for i in shlex.split(cmd_str) if i != '\n']
        run(cmd, check=False)
