from pydantic import BaseModel


class Subtest(BaseModel):
    f4: int

class Test(BaseModel):
    f1: int
    f2: int
    f3: Subtest

def test_fn(**kwargs):
    for k, v in kwargs.items():
        model_config = dict()
        if k in Test.model_fields:
            model_config[k]=v