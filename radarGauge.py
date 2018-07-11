from kivy.config import Config
from kivy.app import App
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.properties import ListProperty
from kivy.uix.widget import Widget
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.label import Label


class radar(Widget):
    unit = NumericProperty(1)
    width_radar = NumericProperty()
    height_radar = NumericProperty()
    value = NumericProperty()


    def __init__(self, **kwargs):
        super(radar, self).__init__(**kwargs)
        
            
        self._radar = ScatterLayout(
            size=(self.width_radar, self.height_radar),
            do_rotate=False, 
            do_scale=False, 
            do_translation=False
            )

        _img_radar = Image(source='radar_1.png', size=(self.width_radar, 
            self.height_radar), allow_stretch=True)


        self._sweeperGauge = ScatterLayout(
            size=(self.width_radar, self.height_radar),
            do_rotate=False,
            do_scale=False,
            do_translation=False
            )

        self._img_sweeper = Image(source='Sweeper.png', size=(self.width_radar, self.height_radar), allow_stretch=True)

        self._radar.add_widget(_img_radar)   
        self.add_widget(self._radar)
        self.add_widget(self._sweeperGauge)
        self._sweeperGauge.add_widget(self._img_sweeper)
        self.bind(pos=self._update)
        self.bind(size=self._update)
        self.bind(value=self._aniSweep)
        
    def _update(self, *args):
        self._radar.pos = self.pos
        self._sweeperGauge.pos = (self.x, self.y)
        self._sweeperGauge.center = self._radar.center


    def _aniSweep(self, *args):
        self._sweeperGauge.rotation = -float(self.value)*self.unit