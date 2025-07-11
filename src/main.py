import os

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk
from tkinterdnd2 import DND_ALL

from config import ConfigMng
from const import APP_HEIGHT, APP_TITLE, APP_WIDTH, ASSETS_DIR
from custom_widgets import CustomScrollableFrame, MyCTkFloatInput, MyCTkIntInput, MyTk
from midi_to_image import Midi2Image
from roll_viewer import RollViewer
from update_checker import NotifyUpdate
from welcome_message import WelcomMessage


class MainFrame():
    def __init__(self, parent) -> None:
        self.parent = parent
        self.conf = ConfigMng()
        self.create_sidebar()
        self.main_view: RollViewer | WelcomMessage = WelcomMessage(self.parent)
        self.midi_file_path = None
        self.change_dark_light_mode(change_state=False)

        # update check
        NotifyUpdate.check(self.conf)
    
    def on_close(self, root):
        # save configs
        # self.conf.dark_mode  (already synchro)
        self.conf.tracker = self.tracker_bar.get()
        self.conf.tempo = int(self.tempo_slider.get())
        self.conf.dpi = int(self.roll_dpi.get())
        self.conf.roll_width = float(self.roll_width.get())
        self.conf.hole_0_center = float(self.hole_0_center.get())
        self.conf.hole_99_center = float(self.hole_99_center.get())
        self.conf.roll_side_margin = float(self.roll_side_margin.get())
        self.conf.hole_width = float(self.hole_width.get())
        self.conf.single_hole_max_len = float(self.single_hole_max_len.get())
        self.conf.chain_perf_spacing = float(self.chain_perf_spacing.get())
        self.conf.shorten_len = int(self.shorten_len.get())
        self.conf.compensate_accel = bool(self.compensate_accel.get())
        self.conf.accel_rate = float(self.accel_rate.get())
        self.conf.save_config()
        root.destroy()

    def change_dark_light_mode(self, change_state: bool = True) -> None:
        if change_state:
            self.conf.dark_mode = not self.conf.dark_mode
        ctk.set_appearance_mode("Dark" if self.conf.dark_mode else "Light")

    def convert(self) -> None:
        if self.midi_file_path is None:
            return

        accel_rate = float(self.accel_rate.get()) / 100 if self.compensate_accel.get() else 0
        converter = Midi2Image(
            int(self.roll_dpi.get()),
            int(self.tempo_slider.get()),
            accel_rate,
            float(self.roll_side_margin.get()),
            float(self.roll_width.get()),
            float(self.hole_width.get()),
            float(self.chain_perf_spacing.get()),
            float(self.single_hole_max_len.get()),
            float(self.hole_0_center.get()),
            float(self.hole_99_center.get()),
            int(self.shorten_len.get()),
            # float(self.roll_start_pad.get()),
            # float(self.roll_end_pad.get()),
        )
        res = converter.convert(self.midi_file_path)
        if not res:
            CTkMessagebox(icon=f"{ASSETS_DIR}/warning_256dp_4B77D1_FILL0_wght400_GRAD0_opsz48.png", title="Conversion Error", message="Conversion Error happened")
            return

        if isinstance(self.main_view, RollViewer):
            self.main_view.set_image(converter.out_img)
        else:
            self.main_view = RollViewer(self.parent, 900, 900, converter.out_img)
        
        self.info_btn.pack(anchor="sw", side="left")

    def _open_file(self, path):
        print(path)
        self.midi_file_path = path
        # change app title
        name = os.path.basename(self.midi_file_path)
        self.parent.title(APP_TITLE + " - " + name)
        self.convert() 

    def file_sel(self):
        if path:= ctk.filedialog.askopenfilename(title="Select a MIDI file", filetypes=[("MIDI file", "*.mid")], initialdir=self.conf.input_dir):
            self._open_file(path)
            self.conf.input_dir = os.path.dirname(path)

    def drop_file(self, event):
        paths: tuple[str] = self.parent.tk.splitlist(event.data)  # parse filepath list
        path = paths[0]  # only one file is supported
        if not path.endswith(".mid"):
            CTkMessagebox(icon=f"{ASSETS_DIR}/warning_256dp_4B77D1_FILL0_wght400_GRAD0_opsz48.png", title="Unsupported File", message="Not MIDI file")
        else:
            self._open_file(path)

    def save_image(self):
        if self.midi_file_path is None:
            return

        name = os.path.basename(self.midi_file_path)
        default_savename = os.path.splitext(name)[0] + f" tempo{self.tempo_slider.get():.0f}.png"
        if path:= ctk.filedialog.asksaveasfilename(title="Save Converted Image", initialfile=default_savename, filetypes=[("PNG file", "*.png")], initialdir=self.conf.output_dir):
            dpi = int(self.roll_dpi.get())
            self.main_view.image.save(path, dpi=(dpi, dpi))
            self.conf.output_dir = os.path.dirname(path)

    def show_image_info(self):
        # show converted image info
        img_w, img_h = self.main_view.image.size
        dpi = int(self.roll_dpi.get())
        length = img_h / dpi / 12  # feet

        msgbox = ctk.CTkToplevel()
        msgbox.geometry("400x120")
        msgbox.title("Image Information")
        msgbox.grab_set()

        font = ctk.CTkFont(size=15)
        ctk.CTkLabel(msgbox, text=f"Image Width: {img_w} px", font=font).pack(padx=10, pady=5, anchor="w")
        ctk.CTkLabel(msgbox, text=f"Image Height: {img_h} px ", font=font).pack(padx=10, pady=5, anchor="w")
        ctk.CTkLabel(msgbox, text=f"Image Length: {length:.2f} feet @{dpi}DPI", font=font).pack(padx=10, pady=5, anchor="w")

    def create_sidebar(self):
        sidebar = CustomScrollableFrame(self.parent, corner_radius=0, fg_color=("#CCCCCC", "#111111"))
        # sidebar = ctk.CTkFrame(self.parent, corner_radius=0, fg_color=("#CCCCCC", "#111111"))
        sidebar.grid(row=0, column=0, sticky="nsew")

        btnimg = ctk.CTkImage(Image.open(f"{ASSETS_DIR}/folder_open_256dp_FFFFFF_FILL0_wght400_GRAD0_opsz48.png"), size=(25, 25))
        self.fileopen = ctk.CTkButton(sidebar, text="Open & Convert MIDI", image=btnimg, command=self.file_sel)
        self.fileopen.pack(padx=10, pady=(10, 0), anchor="w", fill="both")

        ctk.CTkLabel(sidebar, text="Tracker Bar").pack(padx=10, anchor="w")
        self.tracker_bar = ctk.CTkOptionMenu(sidebar, values=["88-Note"])
        self.tracker_bar.set(self.conf.tracker)
        self.tracker_bar.pack(padx=10, anchor="w", fill="both")

        self.tempo_label = ctk.CTkLabel(sidebar, text=f"Tempo:{self.conf.tempo}")
        self.tempo_label.pack(padx=10, anchor="w")
        self.tempo_slider = ctk.CTkSlider(sidebar, from_=30, to=140, number_of_steps=(140 - 30) / 5,  # interval of 5
                                          command=lambda val: self.tempo_label.configure(text=f"Tempo:{val:.0f}"))
        self.tempo_slider.set(self.conf.tempo)
        self.tempo_slider.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Output Image DPI").pack(padx=10, anchor="w")
        self.roll_dpi = MyCTkIntInput(sidebar)
        self.roll_dpi.insert(0, self.conf.dpi)
        self.roll_dpi.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Roll width (inch)").pack(padx=10, anchor="w")
        self.roll_width = MyCTkFloatInput(sidebar)
        self.roll_width.insert(0, self.conf.roll_width)
        self.roll_width.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Hole 0 center position (inch)").pack(padx=10, anchor="w")
        self.hole_0_center = MyCTkFloatInput(sidebar)
        self.hole_0_center.insert(0, self.conf.hole_0_center)
        self.hole_0_center.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Hole 99 center position (inch)").pack(padx=10, anchor="w")
        self.hole_99_center = MyCTkFloatInput(sidebar)
        self.hole_99_center.insert(0, self.conf.hole_99_center)
        self.hole_99_center.pack(padx=10, anchor="w")

        # ctk.CTkLabel(sidebar, text="Padding on roll start (inch)").grid(row=13, column=0, padx=10, sticky="w")
        # self.roll_start_pad = MyCTkFloatInput(sidebar)
        # self.roll_start_pad.insert(0, "2.0")
        # self.roll_start_pad.grid(row=14, column=0, padx=10, sticky="w")

        # ctk.CTkLabel(sidebar, text="Padding on roll end (inch)").grid(row=15, column=0, padx=10, sticky="w")
        # self.roll_end_pad = MyCTkFloatInput(sidebar)
        # self.roll_end_pad.insert(0, "2.0")
        # self.roll_end_pad.grid(row=16, column=0, padx=10, sticky="w")

        ctk.CTkLabel(sidebar, text="Margins on roll sides (inch)").pack(padx=10, anchor="w")
        self.roll_side_margin = MyCTkFloatInput(sidebar)
        self.roll_side_margin.insert(0, self.conf.roll_side_margin)
        self.roll_side_margin.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Hole width (inch)").pack(padx=10, anchor="w")
        self.hole_width = MyCTkFloatInput(sidebar)
        self.hole_width.insert(0, self.conf.hole_width)
        self.hole_width.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Single hole max length (inch)").pack(padx=10, anchor="w")
        self.single_hole_max_len = MyCTkFloatInput(sidebar)
        self.single_hole_max_len.insert(0, self.conf.single_hole_max_len)
        self.single_hole_max_len.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Chain hole spacing (inch)").pack(padx=10, anchor="w")
        self.chain_perf_spacing = MyCTkFloatInput(sidebar)
        self.chain_perf_spacing.insert(0, self.conf.chain_perf_spacing)
        self.chain_perf_spacing.pack(padx=10, anchor="w")

        ctk.CTkLabel(sidebar, text="Shorten hole length (px)").pack(padx=10, anchor="w")
        self.shorten_len = MyCTkIntInput(sidebar)
        self.shorten_len.insert(0, self.conf.shorten_len)
        self.shorten_len.pack(padx=10, anchor="w")

        self.compensate_accel = ctk.CTkSwitch(sidebar, text="Compensate Acceleration")
        if self.conf.compensate_accel:
            self.compensate_accel.select()
        self.compensate_accel.pack(padx=10, pady=(10, 0), anchor="w")

        self.acceleration_rate_label = ctk.CTkLabel(sidebar, text="Acceleration rate (%/feet)")
        self.acceleration_rate_label.pack(padx=25, anchor="w")
        self.accel_rate = MyCTkFloatInput(sidebar)
        self.accel_rate.insert(0, self.conf.accel_rate)
        self.accel_rate.pack(padx=25, anchor="w")

        btnimg = ctk.CTkImage(Image.open(f"{ASSETS_DIR}/refresh_256dp_FFFFFF_FILL0_wght400_GRAD0_opsz48.png"), size=(25, 25))
        cnv_btn = ctk.CTkButton(sidebar, text="Update", image=btnimg, command=self.convert)
        cnv_btn.pack(padx=10, pady=10, anchor="w", fill="both")

        btnimg = ctk.CTkImage(Image.open(f"{ASSETS_DIR}/download_256dp_FFFFFF_FILL0_wght400_GRAD0_opsz48.png"), size=(25, 25))
        save_btn = ctk.CTkButton(sidebar, text="Save Image", image=btnimg, command=self.save_image)
        save_btn.pack(padx=10, pady=10, anchor="w", fill="both")

        btnimg = ctk.CTkImage(light_image=Image.open(f"{ASSETS_DIR}/dark_mode_256dp_1F1F1F_FILL0_wght400_GRAD0_opsz48.png"),
                                        dark_image=Image.open(f"{ASSETS_DIR}/light_mode_256dp_FFFFFF_FILL0_wght400_GRAD0_opsz48.png"), size=(20, 20))
        dark_mode_btn = ctk.CTkButton(sidebar, text="", width=20, fg_color="transparent", hover_color=("gray70", "gray30"), image=btnimg, command=self.change_dark_light_mode)
        dark_mode_btn.pack(anchor="sw", side="left")

        btnimg = ctk.CTkImage(light_image=Image.open(f"{ASSETS_DIR}/info_256dp_000000_FILL0_wght400_GRAD0_opsz48.png"),
                                        dark_image=Image.open(f"{ASSETS_DIR}/info_256dp_FFFFFF_FILL0_wght400_GRAD0_opsz48.png"), size=(20, 20))
        self.info_btn = ctk.CTkButton(sidebar, text="", width=20, fg_color="transparent", hover_color=("gray70", "gray30"), image=btnimg, command=self.show_image_info)
        # dark_mode_btn.pack_forget()


if __name__ == "__main__":
    import sys
    if sys.platform == "darwin" and getattr(sys, 'frozen', False):
        # change current directory for mac binary
        path = sys.argv[0].rsplit("PlaySK Midi to Piano Roll Image Converter.app")[0]
        os.chdir(path)

    app = MyTk()
    app.title(APP_TITLE)
    app.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
    app.wm_iconbitmap()
    app.iconphoto(False, ImageTk.PhotoImage(file=f"{ASSETS_DIR}/PlaySK_icon.ico"))
    app.grid_columnconfigure(0, weight=0)  # sidebar
    app.grid_columnconfigure(1, weight=10)  # Main view
    app.grid_rowconfigure(0, weight=1)

    mainframe = MainFrame(app)

    app.drop_target_register(DND_ALL)
    app.dnd_bind("<<Drop>>", lambda e: mainframe.drop_file(e))
    app.protocol("WM_DELETE_WINDOW", lambda: mainframe.on_close(app))

    app.mainloop()