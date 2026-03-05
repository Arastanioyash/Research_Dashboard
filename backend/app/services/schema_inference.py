from app.models.schema import NetDefinition, Variable


class SchemaInferenceService:
    def infer_variables(self) -> list[Variable]:
        return [Variable(name="respondent_id", dtype="int64", label="Respondent ID")]

    def infer_nets(self) -> list[NetDefinition]:
        return [
            NetDefinition(
                net_name="top2box",
                source_variables=["q1", "q2"],
                aggregation="sum",
            )
        ]


schema_inference_service = SchemaInferenceService()
