import logging
from functools import partial
from pathlib import Path

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

import dataset.decompile as decompile_module
from chisellm.utils.template import load_template, load_template_text, load_text

logger = logging.getLogger(__name__)

cot_template_text = load_template_text(decompile_module, "cot")
instruction_template = load_template(decompile_module, "instruction")

tutorial = load_text(decompile_module, Path("templates") / "tutorial.md")
# HACK: replace at prerender stage
cot_template_text = cot_template_text.replace(r"{#{tutorial}#}", tutorial)


def cot_generation():
    return partial(
        TextGeneration,
        template=cot_template_text,
        columns=["source"],
    )


@step(inputs=["source"], outputs=["instruction"])
def instruction_formation(input: StepInput) -> StepOutput:
    for item in input:
        source = item["source"]
        item["instruction"] = instruction_template.render(source=source)

    yield input


def load(
    llm: LLM,
    *,
    id_column: str = "id",
    source_column: str = "source",
    input_batch_size: int = 128,
) -> Pipeline:
    with Pipeline("chisellm-decompile") as pipeline:
        generate = cot_generation()(
            llm=llm,
            input_mappings={"source": source_column},
            input_batch_size=input_batch_size,
        )
        instruction_format = instruction_formation(
            input_mappings={"source": source_column},
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
        )

        _ = generate >> instruction_format >> sft_format >> keep

    return pipeline
