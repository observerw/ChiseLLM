import logging
from functools import partial

from distilabel.models import LLM
from distilabel.pipeline import Pipeline
from distilabel.steps import (
    FormatTextGenerationSFT,
    KeepColumns,
    StepInput,
    StepOutput,
    step,
)
from distilabel.steps.tasks import TextGeneration

import dataset.completion as design_module
from chisellm.utils.template import load_template, load_template_text

logger = logging.getLogger(__name__)

cot_template_text = load_template_text(design_module, "cot")
instruction_template = load_template(design_module, "instruction")


def cot_generation(mappings: dict[str, str | None] = {}):
    input_mappings = {k: v for k, v in mappings.items() if v}
    columns = list(input_mappings.keys())

    return partial(
        TextGeneration,
        template=cot_template_text,
        input_mappings=input_mappings,
        columns=columns,
    )


@step(inputs=["spec"], outputs=["instruction"])
def instruction_formation(input: StepInput) -> StepOutput:
    for item in input:
        spec = item["spec"]
        item["instruction"] = instruction_template.render(spec=spec)

    yield input


def load(
    name: str,
    llm: LLM,
    *,
    id_column: str = "id",
    spec_column: str = "spec",
    code_column: str | None = None,
    doc_column: str | None = None,
    input_batch_size: int = 128,
):
    with Pipeline(f"chisellm-design-{name}") as pipeline:
        generate = cot_generation(
            {
                "spec": spec_column,
                "code": code_column,
                "doc": doc_column,
            }
        )(
            llm=llm,
            input_batch_size=input_batch_size,
        )

        instruction_format = instruction_formation(
            input_mappings={
                "spec": spec_column,
            },
            input_batch_size=input_batch_size,
        )
        sft_format = FormatTextGenerationSFT(
            input_batch_size=input_batch_size,
        )
        keep = KeepColumns(
            input_mappings={
                "id": id_column,
            },
            columns=[
                "id",
                "prompt",
                "generation",
                "prompt_id",
                "messages",
            ],
            input_batch_size=input_batch_size,
            use_cache=False,
        )

        _ = generate >> instruction_format >> sft_format >> keep

    return pipeline
