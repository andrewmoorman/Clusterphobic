'''
Module docstring
'''
import click
from clusterphobic.submission import Submission
from clusterphobic.clickify import clickify


@click.command()
@clickify(Submission)
def main(**kwargs):
    '''
    Function docstring
    '''
    # kwargs name needs to be the same as Model name in clickify decorator
    submission = kwargs['Submission']
    submission.submit_job()
