import gradio as gr
from langgraph_sidekick.sidekick import SideKick


async def setup():
    sidekick = SideKick()
    await sidekick.setup()
    return sidekick


# Run the sidekick instantiation before the UI
# sidekick = asyncio.run(setup())


def load_sidekick(sidekick):
    print("Loading Sidekick...")
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    result = await sidekick.run_superstep(message=message, success_criteria=success_criteria, history=history)
    return result, sidekick  # Return the graph result and sidekick instannce for further processing


def free_resources(sidekick):
    print("Cleaning up resources...")
    try:
        if sidekick:
            sidekick.free_resources()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


async def reset():
    new_sidekick = SideKick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


# UI
with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick - Your Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)
    # sidekick = gr.State(sidekick, delete_callback=free_resources)  # Initialize with the sidekick instance and set cleanup callback

    # Front-end
    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to your sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False, placeholder="What are the criterias for success?")
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go", variant="primary")

    # Back-end Callbacks
    # Initially loads the setup and returns a sidekick
    ui.load(setup, [], [sidekick])
    # ui.load(load_sidekick, [sidekick], [sidekick])

    message.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    go_button.click(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])
    success_criteria.submit(process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick])

    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])

# launch the UI
ui.launch(inbrowser=True)
