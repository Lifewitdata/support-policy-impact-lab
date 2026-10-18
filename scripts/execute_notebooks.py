"""Execute all notebooks. --in-process works where local kernel sockets are unavailable."""
from pathlib import Path
import argparse
import base64
import io
import os
import nbformat
ROOT=Path(__file__).resolve().parents[1]


def execute_in_process(nb):
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from IPython.display import display, Image
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    shell=InteractiveShell.instance()
    shell.reset(new_session=True)
    def show(*args,**kwargs):
        for number in plt.get_fignums():
            fig=plt.figure(number)
            buffer=io.BytesIO()
            fig.savefig(buffer,format='png',dpi=120,bbox_inches='tight')
            display(Image(data=buffer.getvalue()))
        plt.close('all')
    plt.show=show
    count=0
    for cell in nb.cells:
        if cell.cell_type!='code':continue
        count+=1
        with capture_output(stdout=True,stderr=True,display=True) as captured:
            result=shell.run_cell(cell.source,store_history=True)
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(f'Cell {count} failed: {captured.stdout}\n{captured.stderr}') from (result.error_before_exec or result.error_in_exec)
        cell.execution_count=count
        cell.outputs=[]
        for name,value in [('stdout',captured.stdout),('stderr',captured.stderr)]:
            if value:cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=value))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
    nb.metadata['execution_method']='IPython in-process; every code cell executed; matplotlib PNGs captured'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--in-process',action='store_true')
    args=parser.parse_args()
    os.chdir(ROOT)
    for path in sorted((ROOT/'notebooks').glob('*.ipynb')):
        nb=nbformat.read(path,as_version=4)
        if args.in_process:
            execute_in_process(nb)
        else:
            from nbclient import NotebookClient
            NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
        nbformat.validate(nb)
        nbformat.write(nb,path)
        print('Executed',path.name,flush=True)

if __name__=='__main__':main()
