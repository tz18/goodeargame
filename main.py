'''This is an awful "game" in which you try to guess the notes
in a short randomly generated tune. It is the kind of thing that
I wish I had around as a kid, so that I'd have perfect pitch now.

I used inclement's SparseGridLayout but disfigured it beyond repair
to be a drag and drop grid. It's getting down to the wire here and I'm
lazy so I didn't change any names. I also used code from stocyrs' IcarusTouch
midi keyboard app (which is awesome), in order to initialize the midi stuff.

'''

import pygame.midi
from settingmidi import SettingMIDI
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty, ListProperty, StringProperty
from kivy.event import EventDispatcher
from kivy.uix.behaviors import DragBehavior
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from functools import partial
import random
import time

class SparseGridLayout(FloatLayout):

    rows = NumericProperty(0)
    columns = NumericProperty(0)
    
    shape = ReferenceListProperty(rows, columns)

    def __init__(self,**kwargs):
        super(SparseGridLayout, self).__init__(**kwargs)
        self.grid={}

    def do_layout(self, *args):
        shape_hint = (1. / self.columns, 1. / self.rows)
        for child in self.children:
            child.size_hint = shape_hint
            if not hasattr(child, 'row'):
                child.row = 0
            if not hasattr(child, 'column'):
                child.column = 0

            child.pos_hint = {'x': shape_hint[0] * child.row,
                              'y': shape_hint[1] * child.column}
        super(SparseGridLayout, self).do_layout(*args)
    def add_widget(self,widget,**kwargs):
        super(SparseGridLayout,self).add_widget(widget,**kwargs)
        print("widget.row before sorted is: " + str(widget.row))
        widget.row = sorted((0,widget.row,self.rows-1))[1]
        widget.column = sorted((0,widget.column,self.columns-1))[1]
        print("adding widget to " + str(widget.row) + "," + str(widget.column))
        key = (int(widget.row),int(widget.column))
        if key in self.grid:
            self.grid[key].append(widget)
        else:
            self.grid[key]=[widget]
        print("contents of " + str(key) + ": " +
              str([widget.text for widget in self.grid[key]]))
    def remove_widget(self,widget,**kwargs):
        super(SparseGridLayout,self).remove_widget(widget,**kwargs)
        print("removing widget from " + str(widget.row) + "," + str(widget.column))
        key = (int(widget.row),int(widget.column))
        if key in self.grid:
            self.grid[key].remove(widget)
            if len(self.grid[key])==0:
                del self.grid[key]
                print("removed " + str(key) + " from grid")
            else:
                print("contents of " + str(key) + ": " +
                      str([widget.text for widget in self.grid[key]]))
        
        

class GridLabel(DragBehavior, Button):
    row = NumericProperty(1)
    column = NumericProperty(1)
    gridcoord = ReferenceListProperty(row,column)
    dragginglayout = ObjectProperty(None)
    lockinglayout = ObjectProperty(None)
    freelayouts = ListProperty()

    
    def on_touch_move(self,touch):
        sup = super(GridLabel,self).on_touch_move(touch)
        if self._drag_touch and not (self._drag_touch is not touch or\
                                     self._get_uid('svavoid') in touch.ud):
            print("dragging" + self.text)
            self._old_pos = self.pos
            self.pos_hint={}
            self.parent.remove_widget(self)
            self.dragginglayout.add_widget(self)
        return sup

    def on_touch_up(self,touch):
        if self._drag_touch and not\
        ((self._drag_touch is not touch) or\
         (self._get_uid('svavoid') in touch.ud)):
            sup = super(GridLabel,self).on_touch_up(touch)
            if self._drag_touch == None:
                relativex = self.x/(self.lockinglayout.width
                              + self.lockinglayout.x)
                relativey= self.y/(self.lockinglayout.height
                             + self.lockinglayout.y)
                print("relatives: " + str(relativex) +
                      "," + str(relativey))
                newrow = round(relativex * self.lockinglayout.rows)
                newcolumn = round(relativey * self.lockinglayout.columns)
                self.gridcoord=((newrow,newcolumn))
                print("new grid position: " + str(self.row) +
                      "," + str(self.column))
                self.parent.remove_widget(self)
                if not self.collide_widget(self.lockinglayout):
                    for widget in self.freelayouts:
                        if self.collide_widget(widget):
                            widget.add_widget(self)
                            return sup
                self.lockinglayout.add_widget(self)
            return sup
        else:
            return super(GridLabel,self).on_touch_up(touch)

class ExampleApp(App):
    difficulty=NumericProperty(5)
    attempts=NumericProperty(0)
    lastcorrect=StringProperty(0)
    
    def build(self):
        random.seed(time.time())
        pygame.midi.init()
        self.set_midi_device()
        bl = BoxLayout(orientation="horizontal")
        fl = FloatLayout(size_hint=(.7,1))
        layout = SparseGridLayout(rows=16, columns=16)
        
        labels = []
        self.challenge=set()
        notebox = FloatLayout()
        for i in range(3):
            for j in range(3):
                labels.append(GridLabel(row=i, column=j,
                                        dragginglayout=fl, lockinglayout=layout,freelayouts=[notebox]))
        for label in labels:
            layout.add_widget(label)
        fl.add_widget(layout)
        bl.add_widget(fl)
        bbbl=BoxLayout(orientation="vertical",size_hint=(.3,1))
        topbox=BoxLayout(orientation="horizontal",size_hint=(1,.15))
        bottombox=BoxLayout(orientation="horizontal",size_hint=(1,.15))
        settingsbtn = Button(size_hint=(1,.5),text="SETTINGS",
                             on_press=self.open_settings)
        cnewbtn = Button(size_hint=(1,.5),text="NEW CHALLENGE",
                         on_press=lambda btn: self.new_challenge(xsize=layout.rows,
                                                                 ysize=layout.columns,
                                                                 difficulty=self.difficulty))
        def playurs():
            self.attempts+=1
            self.play(grid=layout.grid)
            if layout.grid.keys()==list(self.challenge) and list(self.challenge)!=[]:
                goaway = Label(text='I AM A WINNER!')
                youwin = Popup(title='YOU WON!!!!!!',
                               content=goaway,
                               size_hint=(.5, .5), size=(400, 400),auto_dismiss=False)
                fl.add_widget(youwin)
                youwin.pos=fl.center
                Clock.schedule_once(lambda dt: fl.remove_widget(youwin),10)
            self.lastcorrect=str(len(self.challenge&set(layout.grid.keys())))+"/"+str(len(self.challenge))
            print(self.lastcorrect)
        uplaybtn = Button(size_hint=(1,1),text="PLAY YOU",
                          on_press=lambda btn: playurs())
        cplaybtn = Button(size_hint=(1,1),text="PLAY THEM",
                          on_press=lambda btn: self.play(grid=self.challenge))
        def chngdiff(d):
            self.difficulty+=d
            if d>0:
                newnote=GridLabel(row=0, column=0,
                                            dragginglayout=fl, lockinglayout=layout,
                                            freelayouts=[notebox],size_hint=(.05,.05))
                x=notebox.pos[0]+random.randint(0,int(notebox.width))
                y=notebox.pos[1]+random.randint(0,int(notebox.height))
                newnote.pos=(x,y)
                print(str(x)+","+str(y))
                print(newnote.pos)
                notebox.add_widget(newnote)
            difflbl.text="Difficulty: " + str(self.difficulty)
        diffincbtn=Button(size_hint=(1,1),text="HARDER",
                          on_press=lambda btn: chngdiff(1))
        diffdecbtn=Button(size_hint=(1,1),text="EASIER",
                          on_press=lambda btn: chngdiff(-1))
        difflbl=Label(size_hint=(1,.5),text="Difficulty: " + str(self.difficulty))
        self.attemptslbl=Label(size_hint=(1,.5),text="Attempts: " + str(self.attempts))
        self.lastcorrectlbl=Label(size_hint=(1,.5),text="Last time: ")
        lblbox=BoxLayout(orientation="vertical",size_hint=(1,.2))
        lblbox.add_widget(self.attemptslbl)
        lblbox.add_widget(difflbl)
        lblbox.add_widget(self.lastcorrectlbl)
        topbox.add_widget(settingsbtn)
        topbox.add_widget(cnewbtn)
        bottombox.add_widget(cplaybtn)
        bottombox.add_widget(uplaybtn)
        subbottombox=BoxLayout(orientation="horizontal",size_hint=(1,.15))
        subbottombox.add_widget(diffincbtn)
        subbottombox.add_widget(diffdecbtn)
        bbbl.add_widget(topbox)
        bbbl.add_widget(bottombox)
        bbbl.add_widget(lblbox)
        bbbl.add_widget(subbottombox)
        bbbl.add_widget(notebox)
        bl.add_widget(bbbl)
        return bl

    def on_lastcorrect(self,instance,value):
        self.lastcorrectlbl.text="Last time:" + self.lastcorrect
    def on_attempts(self,instance,value):
        self.attemptslbl.text="Attempts:" + str(value)
    
    def build_config(self, config):
        # create the various section for the .ini settings file:
        
        config.adddefaultsection('MIDI')
        config.setdefault('MIDI', 'Device', 'USB Uno MIDI Interface')
        config.setdefault('MIDI', 'Channel', '0')
        config.setdefault('MIDI', 'VoiceMode', 'Polyphonic')
        config.setdefault('MIDI', 'PitchbendRange', '24')
        config.setdefault('MIDI', 'Transpose', '36')
        config.setdefault('MIDI', 'CCController', '1') # inactive if y-axis is 'aftertouch'
        config.setdefault('MIDI', 'Velocity', '127')    
    
    def build_settings(self, settings):
        # register my two custom settingItem classes
        settings.register_type('midi', SettingMIDI)

        # set up the built in settings panel for the application settings (not to be confused with the mySettingsPanel for the appearance settings,
        # for which i developed a custom panel). The sections and keys are exactly the same.
                
        #section "MIDI"
        settings.add_json_panel(
            'MIDI', self.config, data='''[
                    { "type": "midi", "title": "MIDI output device", "desc": "Device to use for MIDI","section": "MIDI", "key": "Device"}]''')

    def on_config_change(self, config, section, key, value):

        token = (section, key)

        if token == ('MIDI', 'Device'):
            self.set_midi_device()
##        elif token == ('MIDI', 'Channel'):
##            # TODO: setting the value to 0 here causes an error?!
##            # config.set('MIDI', 'Channel', boundary(value, 0, 15)
##            pass
##        elif token == ('MIDI', 'VoiceMode'):
##            pass
##        elif token == ('MIDI', 'PitchbendRange'):
##            pass
##        elif token == ('MIDI', 'Transpose'):
##            pass
##        elif token == ('MIDI', 'CCController'): # inactive if y-axis is 'aftertouch'
##            pass
##        elif token == ('MIDI', 'Velocity'):
##            pass
    def set_midi_device(self):
        # take the midi device of the settings file and try to connect to it.
        # If there isn't such a device, connect to the default one.
        
        c = pygame.midi.get_count()
        id_device_from_settings = -1
        #print '%s midi devices found' % c
        for i in range(c):
            #print '%s name: %s input: %s output: %s opened: %s' % (pygame.midi.get_device_info(i))
            if pygame.midi.get_device_info(i)[1] == self.config.get('MIDI', 'Device'):
                # if the device from the settings exists in the computers list, take that!
                id_device_from_settings = i
        
        #print 'Default is %s' % pygame.midi.get_device_info(pygame.midi.get_default_output_id())[1]
        
        if id_device_from_settings <> -1:
            self.midi_device = id_device_from_settings
            print 'MIDI device "%s" found. Connecting.' % pygame.midi.get_device_info(id_device_from_settings)[1]
        else:
            # if it was not in the list, take the default one
            self.midi_device = pygame.midi.get_default_output_id()
            print 'Warning: No MIDI device named "%s" found. Choosing the system default ("%s").' % (self.app.config.get('MIDI', 'Device'), pygame.midi.get_device_info(self.midi_device)[1])
        
        if pygame.midi.get_device_info(self.midi_device)[4] == 1:
            print 'Error: Can''t open the MIDI device - It''s already opened!'

        try:
            self.midi_out = pygame.midi.Output(self.midi_device)
        except Exception as e:
            print("Error: " + str(e))
    def play(self,grid):
        try:
            for key in sorted(grid):
                Clock.schedule_once(lambda dt,k=key[1]: self.midi_out.note_on(k+50,300,1),key[0]*.5)
                Clock.schedule_once(lambda dt,k=key[1]: self.midi_out.note_off(k+50,300,1),key[0]+3)
        except Exception as e:
            print("Error:" + str(e))
        
    def new_challenge(self,xsize,ysize,difficulty):
        self.attempts=0
        challenge=[]
        for _ in range(difficulty):
            challenge.append((random.randint(0,xsize-1),random.randint(0,ysize-1)))
        self.challenge=set(challenge)
        self.play(challenge)
            
            
            
            
        
        
if __name__ == "__main__":
    ExampleApp().run()
