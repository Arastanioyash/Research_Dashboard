from pydantic import BaseModel


class Variable(BaseModel):
    name: str
    dtype: str
    label: str | None = None


class NetDefinition(BaseModel):
    net_name: str
    source_variables: list[str]
    aggregation: str
