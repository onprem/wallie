import wx, os, platform, sys, ctypes

if sys.version_info <= (2, 6):
    import commands as subprocess
else:
    import subprocess

class TestFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)

        # there needs to be an "Images" directory with one or more jpegs in it in the
        # current working directory for this to work
        self.jpgs = GetJpgList(".") # get all the jpegs in the Images directory
        self.CurrentJpg = 0

        self.MaxImageSize = 400
        
        b = wx.Button(self, 0, ">")
        b.Bind(wx.EVT_BUTTON, self.DisplayNext)

        bb = wx.Button(self, 0, "<")
        bb.Bind(wx.EVT_BUTTON, self.DisplayPrevious)

        setw = wx.Button(self, 0, "Set as Wallpaper")
        setw.Bind(wx.EVT_BUTTON, self.SetWallpaper)

        # starting with an EmptyBitmap, the real one will get put there
        # by the call to .DisplayNext()
        self.Image = wx.StaticBitmap(self, bitmap=wx.EmptyBitmap(self.MaxImageSize, self.MaxImageSize))

        self.DisplayNext()

        # Using a Sizer to handle the layout: I never  use absolute positioning
        box = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        
        hbox1.Add(bb, 0, wx.RIGHT | wx.ALL,10)

        


        # adding stretchable space before and after centers the image.
        hbox1.Add((1,1),1)
        hbox1.Add(self.Image, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL | wx.ADJUST_MINSIZE, 10)
        hbox1.Add((1,1),1)

        hbox1.Add(b, 0, wx.LEFT | wx.ALL,10)

        box.Add(hbox1, flag=wx.EXPAND, border=10)
        box.Add(setw, 0, wx.CENTER | wx.ALL,10)

        self.SetSizerAndFit(box)
        
        wx.EVT_CLOSE(self, self.OnCloseWindow)

    def SetWallpaper(self, event=None):

        save_location = self.jpgs[self.CurrentJpg-1]

        supported_linux_desktop_envs = ["gnome", "mate", "kde", "lubuntu"]

        # Check OS and environments
        platform_name = platform.system()
        if platform_name.startswith("Lin"):

            # Check desktop environments for linux
            desktop_environment = detect_desktop_environment()
            if desktop_environment and desktop_environment["name"] in supported_linux_desktop_envs:
                os.system(desktop_environment["command"].format(save_location=save_location))
            else:
                #print("Unsupported desktop environment")
                #print("Trying feh")
                os.system("feh --bg-fill {save_location}".format(save_location=save_location))
                #print("[SUCCESS] done!!")

        # Windows
        if platform_name.startswith("Win"):
            # Python 3.x
            if sys.version_info >= (3, 0):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, save_location, 3)
            # Python 2.x
            else:
                ctypes.windll.user32.SystemParametersInfoA(20, 0, save_location, 3)

        # OS X/macOS
        if platform_name.startswith("Darwin"):
            if args.display == 0:
                command = """
                        osascript -e 'tell application "System Events"
                            set desktopCount to count of desktops
                            repeat with desktopNumber from 1 to desktopCount
                                tell desktop desktopNumber
                                    set picture to "{save_location}"
                                end tell
                            end repeat
                        end tell'
                        """.format(save_location=save_location)
            else:
                command = """osascript -e 'tell application "System Events"
                                set desktopCount to count of desktops
                                tell desktop {display}
                                    set picture to "{save_location}"
                                end tell
                            end tell'""".format(display=args.display,
                                            save_location=save_location)
            os.system(command)

    def DisplayNext(self, event=None):
        # load the image
        Img = wx.Image(self.jpgs[self.CurrentJpg], wx.BITMAP_TYPE_ANY)

        # scale the image, preserving the aspect ratio
        W = Img.GetWidth()
        H = Img.GetHeight()
        if W > H:
            NewW = self.MaxImageSize
            NewH = self.MaxImageSize * H / W
        else:
            NewH = self.MaxImageSize
            NewW = self.MaxImageSize * W / H
        Img = Img.Scale(NewW,NewH)
 
        # convert it to a wx.Bitmap, and put it on the wx.StaticBitmap
        self.Image.SetBitmap(wx.BitmapFromImage(Img))

        # You can fit the frame to the image, if you want.
        self.Fit()
        self.Layout()
        self.Refresh()

        self.CurrentJpg += 1
        if self.CurrentJpg > len(self.jpgs) -1:
            self.CurrentJpg = 0

    def DisplayPrevious(self, event=None):
        # load the image
        Img = wx.Image(self.jpgs[self.CurrentJpg - 2], wx.BITMAP_TYPE_ANY)

        # scale the image, preserving the aspect ratio
        W = Img.GetWidth()
        H = Img.GetHeight()
        if W > H:
            NewW = self.MaxImageSize
            NewH = self.MaxImageSize * H / W
        else:
            NewH = self.MaxImageSize
            NewW = self.MaxImageSize * W / H
        Img = Img.Scale(NewW,NewH)
 
        # convert it to a wx.Bitmap, and put it on the wx.StaticBitmap
        self.Image.SetBitmap(wx.BitmapFromImage(Img))

        # You can fit the frame to the image, if you want.
        self.Fit()
        self.Layout()
        self.Refresh()

        self.CurrentJpg -= 1
        if self.CurrentJpg < 0:
            self.CurrentJpg = len(self.jpgs) -1

    def OnCloseWindow(self, event):
        self.Destroy()

def detect_desktop_environment():
    """Get current Desktop Environment
       http://stackoverflow.com
       /questions/2035657/what-is-my-current-desktop-environment
    :return: environment
    """
    environment = {}
    if os.environ.get("KDE_FULL_SESSION") == "true":
        environment["name"] = "kde"
        environment["command"] = """
                    qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
                        var allDesktops = desktops();
                        print (allDesktops);
                        for (i=0;i<allDesktops.length;i++) {{
                            d = allDesktops[i];
                            d.wallpaperPlugin = "org.kde.image";
                            d.currentConfigGroup = Array("Wallpaper",
                                                   "org.kde.image",
                                                   "General");
                            d.writeConfig("Image", "file:///{save_location}")
                        }}
                    '
                """
    elif os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        environment["name"] = "gnome"
        environment["command"] = "gsettings set org.gnome.desktop.background picture-uri file://{save_location}"
    elif os.environ.get("DESKTOP_SESSION") == "Lubuntu":
        environment["name"] = "lubuntu"
        environment["command"] = "pcmanfm -w {save_location} --wallpaper-mode=fit"
    elif os.environ.get("DESKTOP_SESSION") == "mate":
        environment["name"] = "mate"
        environment["command"] = "gsettings set org.mate.background picture-filename {save_location}"
    else:
        try:
            info = subprocess.getoutput("xprop -root _DT_SAVE_MODE")
            if ' = "xfce4"' in info:
                environment["name"] = "xfce"
        except (OSError, RuntimeError):
            environment = None
            pass
    return environment

def GetJpgList(dir):
    jpgs = [f for f in os.listdir(dir) if (f[-4:] == ".jpg" or f[-4:] == ".png")]
    # print "JPGS are:", jpgs
    return [os.path.join(dir, f) for f in jpgs]

class App(wx.App):
    def OnInit(self):

        frame = TestFrame(None, -1, "wxBitmap Test", wx.DefaultPosition,(550,200))
        self.SetTopWindow(frame)
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = App(0)
    app.MainLoop()