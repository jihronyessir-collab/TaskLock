"""Render a distinctive TaskLock v5 BLUECORE lock emblem (PNG + multi-size ICO)."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math
S=1024
out=Path(__file__).resolve().parents[1]/'assets'
out.mkdir(parents=True,exist_ok=True)
base=Image.new('RGBA',(S,S),(0,0,0,0))
d=ImageDraw.Draw(base)
# Rounded dark tile with a layered navy inset.
d.rounded_rectangle((30,30,994,994),radius=225,fill='#081227',outline='#1D518A',width=8)
d.rounded_rectangle((65,65,959,959),radius=185,fill='#0D2040',outline='#16365F',width=3)
# inner ambient glow
halo=Image.new('RGBA',(S,S),(0,0,0,0)); h=ImageDraw.Draw(halo)
h.ellipse((205,155,819,790),fill=(15,130,255,80))
halo=halo.filter(ImageFilter.GaussianBlur(110)); base=Image.alpha_composite(base,halo)
# electric circuit trim and bracket accents
trim=ImageDraw.Draw(base)
trim.arc((158,125,865,855),start=215,end=330,fill='#246CC1',width=13)
trim.line([(210,774),(294,774)],fill='#1E6BB7',width=10)
trim.ellipse((281,761,306,786),fill='#48BEFF')
trim.line([(727,257),(812,257)],fill='#1E6BB7',width=10)
trim.ellipse((714,244,740,270),fill='#48BEFF')
# glow shackle
shadow=Image.new('RGBA',(S,S),(0,0,0,0));sd=ImageDraw.Draw(shadow)
sd.arc((320,203,704,670),180,360,fill=(55,180,255,185),width=107)
shadow=shadow.filter(ImageFilter.GaussianBlur(34));base=Image.alpha_composite(base,shadow)
d=ImageDraw.Draw(base)
d.arc((319,208,705,673),180,360,fill='#37B3FF',width=82)
d.arc((334,223,690,660),180,360,fill='#B0E9FF',width=20)
d.rounded_rectangle((251,451,773,819),radius=75,fill='#123F82',outline='#63D1FF',width=14)
d.rounded_rectangle((280,473,746,789),radius=57,fill='#176ED4',outline='#2D99EE',width=5)
# subtle diagonal band
d.polygon([(315,503),(700,503),(692,560),(310,607)],fill='#2083E9')
# keyhole (circle + narrower flared stem)
d.ellipse((459,574,565,680),fill='#05172F')
d.polygon([(483,653),(541,653),(566,749),(457,749)],fill='#05172F')
d.ellipse((478,592,546,660),fill='#64CDFF')
d.ellipse((493,605,531,644),fill='#041528')
d.line([(310,761),(695,761)],fill='#389CED',width=6)
# glow treated conservatively so the icon remains clear small
base.save(out/'tasklock.png')
base.convert('RGBA').save(out/'tasklock.ico',format='ICO',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
# transparent standalone mark for the site (no existing feather)
base.resize((512,512),Image.Resampling.LANCZOS).save(out/'tasklock-512.png')
print('Wrote new icon')
