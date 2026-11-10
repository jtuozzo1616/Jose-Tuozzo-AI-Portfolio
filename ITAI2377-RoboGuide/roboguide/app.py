"""Launch via `python -m roboguide.app`. Use locally, not on a robot."""
from .core import RoboGuide

def launch():
    import gradio as gr
    engine=RoboGuide()
    def respond(question,version):
        result=engine.ask(question,version=None if version=='Unknown' else version)
        refs='\n'.join(f'- [{x["title"]}]({x["url"]})' for x in result.references) or 'No evidence selected.'
        return result.answer, f'{result.status} | evidence strength {result.evidence_strength:.2f} (not calibrated)', refs
    with gr.Blocks(title='RoboGuide · evidence-first PiDog support') as demo:
        gr.Markdown('# RoboGuide AI\nOfficial-source, CPU-first technical support for PiDog. **No robot control or remote command execution.**')
        question=gr.Textbox(label='Question / traceback',lines=3,placeholder='My V2 PiDog zero button works but calibrate script does not move the servos')
        version=gr.Dropdown(['Unknown','standard','v2'],value='Unknown',label='Hardware version')
        btn=gr.Button('Find documented troubleshooting steps',variant='primary')
        answer=gr.Textbox(label='Evidence-based response',lines=12)
        status=gr.Textbox(label='Retrieval status')
        refs=gr.Markdown(label='Sources')
        btn.click(respond,inputs=[question,version],outputs=[answer,status,refs])
        gr.Examples([['PiDog wobbles when standing','Unknown'],['My V2 zero button works but Python control fails','v2'],['How to make ten push_up actions?','Unknown'],['The touch sensor is always HIGH','Unknown'],['Ultrasonic reads -1','Unknown']],inputs=[question,version])
    demo.launch()
if __name__=='__main__':launch()
