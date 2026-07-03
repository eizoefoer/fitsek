#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import csv, shutil
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'; OUT=SITE/'assets/social'

def font(size, bold=False):
    for p in [('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf')]:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def wrap(draw,text,fnt,max_width):
    words=text.split(); lines=[]; cur=''
    for w in words:
        test=(cur+' '+w).strip()
        if draw.textbbox((0,0),test,font=fnt)[2] <= max_width: cur=test
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def bg(w,h):
    img=Image.new('RGB',(w,h),'#05070c')
    glow=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(glow,'RGBA')
    d.ellipse((-260,-180,620,610),fill=(124,92,255,72))
    d.ellipse((520,-120,1320,560),fill=(66,245,167,56))
    d.ellipse((250,720,1280,1580),fill=(66,217,255,38))
    glow=glow.filter(ImageFilter.GaussianBlur(70))
    img=Image.alpha_composite(img.convert('RGBA'),glow).convert('RGB')
    return img

def cta_label(raw):
    r=(raw or '').lower()
    if '12-week' in r or 'waitlist' in r: return 'Join the 12-week waitlist →'
    if 'save' in r: return 'Save this checklist →'
    if 'comment' in r: return 'Comment RESET →'
    if 'share' in r: return 'Share this with a desk worker →'
    return 'Get the free 7-Day Reset →'

def draw_button_text(d, box, text):
    x1,y1,x2,y2=box
    sizes=[36,33,30,27,24]
    for s in sizes:
        f=font(s,True)
        lines=wrap(d,text,f,x2-x1-80)
        if len(lines)<=2 and len(lines)*s*1.25 <= (y2-y1-22):
            total=len(lines)*int(s*1.2)
            y=y1+(y2-y1-total)//2-2
            for line in lines:
                tw=d.textbbox((0,0),line,font=f)[2]
                d.text((x1+(x2-x1-tw)//2,y),line,font=f,fill=(5,7,12,255)); y+=int(s*1.2)
            return

def create(path,title,hook,cta,day):
    w,h=1080,1350; img=bg(w,h); d=ImageDraw.Draw(img,'RGBA')
    d.rounded_rectangle((54,62,w-54,h-62),radius=54,fill=(13,20,34,218),outline=(255,255,255,34),width=2)
    d.rounded_rectangle((86,96,156,166),radius=22,fill=(185,255,74,255)); d.text((111,104),'F',font=font(44,True),fill=(5,7,12,255))
    d.text((176,112),'FITSEK',font=font(34,True),fill=(245,248,255,255)); d.text((w-222,117),f'DAY {day:02d}',font=font(28,True),fill=(185,255,74,230))
    y=250; d.text((86,y),title.upper(),font=font(38,True),fill=(66,245,167,255)); y+=86
    hook_font=font(62,True)
    for line in wrap(d,hook,hook_font,w-190)[:7]: d.text((86,y),line,font=hook_font,fill=(245,248,255,255)); y+=76
    cy=900; d.rounded_rectangle((86,cy,w-86,cy+180),radius=30,fill=(5,7,12,190),outline=(255,255,255,40),width=2)
    d.text((126,cy+38),'Desk-day recomp system',font=font(38,True),fill=(245,248,255,255)); d.text((126,cy+98),'Strength • steps • protein • weekly review',font=font(29),fill=(169,183,202,255))
    box=(86,1132,w-86,1240); d.rounded_rectangle(box,radius=54,fill=(185,255,74,255)); draw_button_text(d,box,cta_label(cta))
    d.text((86,1272),'Illustrative fitness education only. Results vary.',font=font(23),fill=(169,183,202,220))
    img.save(path,quality=92)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=list(csv.DictReader((ROOT/'content/social/30-day-calendar.csv').open(newline='',encoding='utf-8')))
    for r in rows:
        day=int(r['day']); create(OUT/f'post-{day:02d}.png',r.get('post_title','Fitsek'),r.get('hook',''),r.get('cta',''),day)
    # OG + avatar
    og=bg(1200,630); d=ImageDraw.Draw(og,'RGBA'); d.rounded_rectangle((58,58,1142,572),radius=44,fill=(13,20,34,220),outline=(255,255,255,40),width=2)
    d.rounded_rectangle((94,96,174,176),radius=24,fill=(185,255,74,255)); d.text((123,104),'F',font=font(52,True),fill=(5,7,12,255)); d.text((198,112),'FITSEK',font=font(44,True),fill=(245,248,255,255)); d.text((94,230),'Recomp that fits\nreal work weeks.',font=font(72,True),fill=(245,248,255,255),spacing=6); d.text((94,438),'Strength • steps • protein • weekly review',font=font(34),fill=(66,245,167,255)); og.save(OUT/'og-fitsek.png',quality=92)
    av=bg(1080,1080); d=ImageDraw.Draw(av,'RGBA'); d.rounded_rectangle((180,180,900,900),radius=210,fill=(185,255,74,255)); d.text((428,300),'F',font=font(420,True),fill=(5,7,12,255)); av.save(OUT/'avatar-fitsek.png',quality=92)
    print(f'rendered {len(rows)} social posts + og/avatar to {OUT}')
if __name__=='__main__': main()
