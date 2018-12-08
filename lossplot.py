import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np

class LossPlot:
    def __init__(self,alpha=0.4,smooth=0,single_select=False,title='Loss Polt'):
        self.records = []
        self.alpha = alpha
        self.single_select = single_select
        self.smooth = smooth
        self.ID = 0
        self.first_click = True

        self.fig, (self.ax, self.ax_text) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]},figsize=(16, 8))
        self.mono = {'family': 'monospace'}  # text align
        self.ax.set_title(title)
        self.ax_text.set_title('Summary')
        self.ax_text.set_xticks([])
        self.ax_text.set_yticks([])

        self.print_()

    def print_(self):
        print('Note:')
        print('1.select cruves by click curve or legend(deep color means selected)')
        print("2.single select mode can be set by 'single_select=True', defalut False")
        print('3.compare only in selected curves')
        print('4.Config & Curve Summary will print last click curve no matter whether it be selected')

    def record_summary(self,record):
        min_data = min(record,key=lambda x:x[1])
        max_data = max(record,key=lambda x:x[1])
        return {'min':min_data,'max':max_data}


    def append(self,record,name=None,color=None,note=None):
        record = np.asarray(record)
        summary = self.record_summary(record)
        self.records.append({'record':record,'color':color,'name':name,'note':note,'summary':summary})
        self.ID += 1

    def window_smooth(self,record):
        res = np.copy(record)
        for i in range(record.shape[0]):
            window_min = max(0,i-self.smooth)
            window_max = min(record.shape[0]-1,i+self.smooth)+1
            res[i,1] = np.mean(res[window_min:window_max,1])
        return res

    def get_curve_summary_string(self,name,note,summary):
        string = 'Config:{}\n'.format(name)
        if isinstance(note,str):
            string += note
        elif isinstance(note,dict):
            for i,v in note.items():
                string += '{:<20}:{:<10}\n'.format(i,v)
        else:
            string += 'None\n'

        min_data = summary['min']
        max_data = summary['max']
        string += '\nCurve Summary:{}\n'.format(name)
        string += 'Min Value:{:>8.5f} at step {:<5d}\n'.format(min_data[1],int(min_data[0]))
        string += 'Max Value:{:>8.5f} at step {:<5d}\n'.format(max_data[1],int(max_data[0]))

        return string

    def get_summary_string(self, ):
        min_value = np.inf
        min_cruve = None
        max_value = -np.inf
        max_cruve = None
        for r, s in zip(self.records, self.curves_select):
            if s:
                if r['summary']['max'][1] > max_value:
                    max_cruve = r['name']
                if r['summary']['min'][1] < min_value:
                    min_cruve = r['name']
        string = 'Summary:\n\n'
        string += 'Max Value in Curve:{}\n'.format(max_cruve)
        string += 'Min Value in Curve:{}\n'.format(min_cruve)
        string += '\nNote: compare only in selected\n      curves'

        return string

    def set_carve_summary(self,string):
        self.ax_text.set_xticks([])
        self.ax_text.set_yticks([])
        self.ax_text.text(0.03, 0.98, string,horizontalalignment='left',verticalalignment='top',fontdict=self.mono)

    def set_summary(self,string):
        self.ax_text.set_xticks([])
        self.ax_text.set_yticks([])
        self.ax_text.text(0.03, 0.3, string,horizontalalignment='left',verticalalignment='top',fontdict=self.mono)

    def init_fig(self,):
        self.curves = []
        self.curves_select = [True for i in range(self.ID)]
        for curve_data in self.records:
            r = self.window_smooth(curve_data['record'])
            c, = self.ax.plot(r[:,0],r[:,1],lw=1,color=curve_data['color'],label=str(curve_data['name'])) # 注意!要个','
            self.curves.append(c)

        leg = self.ax.legend(loc='upper left', fancybox=True, shadow=True)
        leg.get_frame().set_alpha(0.8)

        self.leglines = leg.get_lines()

        self.legline2ID = {}
        for i,legline in enumerate(self.leglines):
            legline.set_picker(5)
            self.legline2ID[legline] = i

        self.line2ID = {}
        for i,line in enumerate(self.curves):
            line.set_picker(5)
            self.line2ID[line] = i

        global button  # must global
        point = plt.axes([0.3, 0.03, 0.1, 0.03])
        button = Button(point, "reset")
        button.on_clicked(self.reset_clicked)

        self.set_carve_summary('No Select')
        self.set_summary(self.get_summary_string())

    def reset_clicked(self,event):
        self.first_click = True
        for i in range(self.ID):
            self.leglines[i].set_alpha(1)
            self.curves[i].set_alpha(1)

        for i,_ in enumerate(self.curves_select):
            self.curves_select[i] = True

        self.ax_text.cla()
        self.set_carve_summary('No Select')
        self.set_summary(self.get_summary_string())
        self.fig.canvas.draw()

    def onpick(self,event, ):
        click = event.artist

        # reset
        if self.single_select:
            self.curves_select = [False for i in range(self.ID)]
        else:
            if self.first_click:
                self.curves_select = [False for i in range(self.ID)]
                self.first_click = False

        if click in self.legline2ID:
            ID = self.legline2ID[click]
            self.curves_select[ID] = not self.curves_select[ID]
        elif click in self.line2ID:
            ID = self.line2ID[click]
            self.curves_select[ID] = not self.curves_select[ID]

        # re-plot
        for i in range(self.ID):
            if self.curves_select[i]:
                self.leglines[i].set_alpha(1)
                self.curves[i].set_alpha(1)
            else:
                self.leglines[i].set_alpha(self.alpha)
                self.curves[i].set_alpha(self.alpha)

        note = self.records[ID]['note']
        summary = self.records[ID]['summary']
        name = self.records[ID]['name']
        note = self.get_curve_summary_string(name,note,summary)
        summary = self.get_summary_string()
        self.ax_text.cla()
        self.set_carve_summary(note)
        self.set_summary(summary)
        self.fig.canvas.draw()

    def show(self):
        self.init_fig()
        self.fig.canvas.mpl_connect('pick_event', self.onpick)

        plt.show()




if __name__ == '__main__':
    import pickle

    x = np.arange(0,1000,10)
    y1 = [np.sin(i/100) for i in x]
    y2 = [2 * np.sin(i/200) for i in x]
    y3 = [0.5 * np.sin(i/300) for i in x]

    record1 = list(zip(x,y1))
    record2 = list(zip(x,y2))
    record3 = list(zip(x,y3))

    ploter = LossPlot(alpha=0.2,single_select=True,smooth=0)

    ploter.append(record1,color='red',name='record1',note={'lr':0.01,'batch_size':64,'weight_decay':1e-3})
    ploter.append(record2,color='blue',name='record2',note={'asd':10,'aa':'asd','zx':12312})
    ploter.append(record3,color=None,name='record3',note={'1':10,'2':'asd','3':0.312})


    ploter.show()