import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os
import threading
import time
import math
from datetime import datetime, timedelta
import winsound
from typing import Dict, List, Optional

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class HIITTimer:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("HIIT Me Up")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Timer state
        self.is_running = False
        self.is_paused = False
        self.current_set = 0
        self.current_rep = 0
        self.time_remaining = 0
        self.total_elapsed = 0
        self.timer_thread = None
        self.start_time = None
        
        # Workout data
        self.sets = 1
        self.reps = []  # List of {'name': str, 'duration': int}
        self.workout_history = []
        
        # Settings
        self.settings_file = "hiit_settings.json"
        self.workouts_file = "hiit_workouts.json"
        self.history_file = "hiit_history.json"
        self.dark_mode = True
        
        self.load_settings()
        self.setup_ui()
        self.load_saved_workouts()
        
    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ctk.CTkTabview(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Setup tabs
        self.setup_tab = self.notebook.add("Setup")
        self.timer_tab = self.notebook.add("Timer")
        self.history_tab = self.notebook.add("History")
        
        self.setup_setup_tab()
        self.setup_timer_tab()
        self.setup_history_tab()
        
    def setup_setup_tab(self):
        # Top controls frame
        top_frame = ctk.CTkFrame(self.setup_tab)
        top_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Dark mode toggle
        self.dark_mode_var = ctk.BooleanVar(value=self.dark_mode)
        dark_mode_switch = ctk.CTkSwitch(
            top_frame, 
            text="Dark Mode", 
            variable=self.dark_mode_var,
            command=self.toggle_dark_mode
        )
        dark_mode_switch.pack(side="right", padx=10, pady=10)
        
        # Quick Tabata button
        tabata_btn = ctk.CTkButton(
            top_frame,
            text="⚡ Quick Tabata",
            command=self.quick_tabata,
            fg_color="#FF6B35",
            hover_color="#E55A2B"
        )
        tabata_btn.pack(side="left", padx=10, pady=10)
        
        # Sets configuration
        sets_frame = ctk.CTkFrame(self.setup_tab)
        sets_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(sets_frame, text="Number of Sets:").pack(side="left", padx=10, pady=10)
        self.sets_var = ctk.IntVar(value=1)
        sets_spinbox = ctk.CTkEntry(sets_frame, textvariable=self.sets_var, width=60)
        sets_spinbox.pack(side="left", padx=5, pady=10)
        
        # Reps configuration
        reps_frame = ctk.CTkFrame(self.setup_tab)
        reps_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(reps_frame, text="Reps Configuration:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Reps list with scrollbar
        self.reps_frame = ctk.CTkScrollableFrame(reps_frame, height=200)
        self.reps_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add rep button
        add_rep_btn = ctk.CTkButton(reps_frame, text="+ Add Rep", command=self.add_rep)
        add_rep_btn.pack(pady=5)
        
        # Preview and control buttons
        buttons_frame = ctk.CTkFrame(self.setup_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        preview_btn = ctk.CTkButton(buttons_frame, text="Preview Workout", command=self.preview_workout)
        preview_btn.pack(side="left", padx=5, pady=10)
        
        save_btn = ctk.CTkButton(buttons_frame, text="Save Workout", command=self.save_workout)
        save_btn.pack(side="left", padx=5, pady=10)
        
        load_btn = ctk.CTkButton(buttons_frame, text="Load Workout", command=self.load_workout)
        load_btn.pack(side="left", padx=5, pady=10)
        
        start_btn = ctk.CTkButton(
            buttons_frame, 
            text="🏃 Start Workout", 
            command=self.start_workout,
            fg_color="#4CAF50",
            hover_color="#45A049"
        )
        start_btn.pack(side="right", padx=5, pady=10)
        
        # Initialize with one rep
        self.add_rep()
        
    def setup_timer_tab(self):
        # Main timer display
        timer_frame = ctk.CTkFrame(self.timer_tab)
        timer_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Current rep name
        self.current_rep_label = ctk.CTkLabel(
            timer_frame, 
            text="Ready to Start", 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.current_rep_label.pack(pady=(20, 10))
        
        # Time remaining (big display)
        self.time_display = ctk.CTkLabel(
            timer_frame, 
            text="00:00", 
            font=ctk.CTkFont(size=72, weight="bold")
        )
        self.time_display.pack(pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(timer_frame, width=400, height=20)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Set and rep info
        self.set_rep_label = ctk.CTkLabel(timer_frame, text="", font=ctk.CTkFont(size=16))
        self.set_rep_label.pack(pady=5)
        
        # Time info frame
        time_info_frame = ctk.CTkFrame(timer_frame)
        time_info_frame.pack(pady=10)
        
        self.elapsed_label = ctk.CTkLabel(time_info_frame, text="Elapsed: 00:00:00")
        self.elapsed_label.pack(side="left", padx=20)
        
        self.remaining_label = ctk.CTkLabel(time_info_frame, text="Remaining: 00:00:00")
        self.remaining_label.pack(side="right", padx=20)
        
        # Control buttons
        controls_frame = ctk.CTkFrame(timer_frame)
        controls_frame.pack(pady=20)
        
        self.pause_btn = ctk.CTkButton(
            controls_frame, 
            text="⏸️ Pause", 
            command=self.pause_resume_timer,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=10)
        
        self.reset_btn = ctk.CTkButton(
            controls_frame, 
            text="🔄 Reset", 
            command=self.reset_timer,
            fg_color="#FF5722",
            hover_color="#E64A19"
        )
        self.reset_btn.pack(side="left", padx=10)
        
    def setup_history_tab(self):
        history_frame = ctk.CTkFrame(self.history_tab)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(history_frame, text="Workout History", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        # History list
        self.history_frame = ctk.CTkScrollableFrame(history_frame)
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Export button
        export_btn = ctk.CTkButton(history_frame, text="Export History", command=self.export_history)
        export_btn.pack(pady=10)
        
        self.load_history()
        
    def add_rep(self):
        rep_frame = ctk.CTkFrame(self.reps_frame)
        rep_frame.pack(fill="x", padx=5, pady=2)
        
        # Rep number
        rep_num = len(self.reps_frame.winfo_children())
        ctk.CTkLabel(rep_frame, text=f"Rep {rep_num}:", width=60).pack(side="left", padx=5, pady=5)
        
        # Name entry
        name_entry = ctk.CTkEntry(rep_frame, placeholder_text="Exercise name", width=150)
        name_entry.pack(side="left", padx=5, pady=5)
        name_entry.insert(0, "Work" if rep_num % 2 == 1 else "Rest")
        
        # Duration entry
        duration_entry = ctk.CTkEntry(rep_frame, placeholder_text="Seconds", width=80)
        duration_entry.pack(side="left", padx=5, pady=5)
        duration_entry.insert(0, "30" if rep_num % 2 == 1 else "10")
        
        # Delete button
        delete_btn = ctk.CTkButton(
            rep_frame, 
            text="❌", 
            width=30, 
            command=lambda: self.delete_rep(rep_frame)
        )
        delete_btn.pack(side="right", padx=5, pady=5)
        
    def delete_rep(self, rep_frame):
        rep_frame.destroy()
        self.update_rep_numbers()
        
    def update_rep_numbers(self):
        for i, child in enumerate(self.reps_frame.winfo_children()):
            label = child.winfo_children()[0]
            label.configure(text=f"Rep {i+1}:")
            
    def get_reps_data(self):
        reps = []
        for child in self.reps_frame.winfo_children():
            widgets = child.winfo_children()
            if len(widgets) >= 3:
                name = widgets[1].get().strip()
                try:
                    duration = int(widgets[2].get())
                    if name and duration > 0:
                        reps.append({"name": name, "duration": duration})
                except ValueError:
                    continue
        return reps
        
    def quick_tabata(self):
        # Clear existing reps
        for child in self.reps_frame.winfo_children():
            child.destroy()
            
        # Set 8 rounds
        self.sets_var.set(8)
        
        # Add work and rest reps
        for i in range(2):
            self.add_rep()
            
        # Set tabata values
        children = self.reps_frame.winfo_children()
        children[0].winfo_children()[1].delete(0, 'end')
        children[0].winfo_children()[1].insert(0, "Work")
        children[0].winfo_children()[2].delete(0, 'end')
        children[0].winfo_children()[2].insert(0, "20")
        
        children[1].winfo_children()[1].delete(0, 'end')
        children[1].winfo_children()[1].insert(0, "Rest")
        children[1].winfo_children()[2].delete(0, 'end')
        children[1].winfo_children()[2].insert(0, "10")
        
        # Start workout immediately
        self.start_workout()
        
    def preview_workout(self):
        reps = self.get_reps_data()
        sets = self.sets_var.get()
        
        if not reps:
            messagebox.showwarning("No Reps", "Please add at least one rep.")
            return
            
        total_time = sum(rep["duration"] for rep in reps) * sets
        
        preview_text = f"Workout Preview:\n\n"
        preview_text += f"Sets: {sets}\n"
        preview_text += f"Total Time: {self.format_time(total_time)}\n\n"
        preview_text += "Reps per set:\n"
        
        for i, rep in enumerate(reps, 1):
            preview_text += f"{i}. {rep['name']} - {rep['duration']}s\n"
            
        messagebox.showinfo("Workout Preview", preview_text)
        
    def start_workout(self):
        reps = self.get_reps_data()
        sets = self.sets_var.get()
        
        if not reps:
            messagebox.showwarning("No Reps", "Please add at least one rep.")
            return
            
        self.reps = reps
        self.sets = sets
        self.current_set = 0
        self.current_rep = 0
        self.total_elapsed = 0
        self.start_time = time.time()
        
        # Switch to timer tab
        self.notebook.set("Timer")
        
        # Start the timer
        self.is_running = True
        self.is_paused = False
        self.pause_btn.configure(state="normal")
        
        self.start_current_rep()
        
    def start_current_rep(self):
        if self.current_set >= self.sets:
            self.workout_complete()
            return
            
        if self.current_rep >= len(self.reps):
            self.current_set += 1
            self.current_rep = 0
            if self.current_set >= self.sets:
                self.workout_complete()
                return
                
        current = self.reps[self.current_rep]
        self.time_remaining = current["duration"]
        
        # Update display
        self.current_rep_label.configure(text=current["name"])
        self.set_rep_label.configure(text=f"Set {self.current_set + 1} of {self.sets} — {current['name']}")
        
        # Change color based on exercise type
        if "rest" in current["name"].lower():
            self.current_rep_label.configure(text_color="#4FC3F7")
        else:
            self.current_rep_label.configure(text_color="#FF5722")
            
        # Play beep
        self.play_beep()
        
        # Start timer thread
        if self.timer_thread and self.timer_thread.is_alive():
            return
            
        self.timer_thread = threading.Thread(target=self.run_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
    def run_timer(self):
        while self.is_running and self.time_remaining > 0:
            if not self.is_paused:
                self.root.after(0, self.update_display)
                time.sleep(1)
                self.time_remaining -= 1
                self.total_elapsed += 1
            else:
                time.sleep(0.1)
                
        if self.is_running and self.time_remaining <= 0:
            self.current_rep += 1
            self.root.after(0, self.start_current_rep)
            
    def update_display(self):
        # Update time display
        self.time_display.configure(text=self.format_time_mm_ss(self.time_remaining))
        
        # Update progress bar
        if self.reps and self.current_rep < len(self.reps):
            current_duration = self.reps[self.current_rep]["duration"]
            progress = 1 - (self.time_remaining / current_duration)
            self.progress_bar.set(progress)
            
        # Update elapsed and remaining time
        self.elapsed_label.configure(text=f"Elapsed: {self.format_time(self.total_elapsed)}")
        
        total_workout_time = sum(rep["duration"] for rep in self.reps) * self.sets
        remaining_workout_time = total_workout_time - self.total_elapsed
        self.remaining_label.configure(text=f"Remaining: {self.format_time(remaining_workout_time)}")
        
    def pause_resume_timer(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.configure(text="▶️ Resume")
        else:
            self.pause_btn.configure(text="⏸️ Pause")
            
    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.current_set = 0
        self.current_rep = 0
        self.time_remaining = 0
        self.total_elapsed = 0
        
        self.current_rep_label.configure(text="Ready to Start", text_color="white")
        self.time_display.configure(text="00:00")
        self.set_rep_label.configure(text="")
        self.elapsed_label.configure(text="Elapsed: 00:00:00")
        self.remaining_label.configure(text="Remaining: 00:00:00")
        self.progress_bar.set(0)
        self.pause_btn.configure(text="⏸️ Pause", state="disabled")
        
    def workout_complete(self):
        self.is_running = False
        self.current_rep_label.configure(text="🎉 Workout Complete!", text_color="#4CAF50")
        self.time_display.configure(text="DONE")
        self.pause_btn.configure(state="disabled")
        
        # Save to history
        workout_data = {
            "date": datetime.now().isoformat(),
            "sets": self.sets,
            "reps": self.reps,
            "total_time": self.total_elapsed
        }
        self.workout_history.append(workout_data)
        self.save_history()
        self.load_history()
        
        # Play completion sound
        for _ in range(3):
            self.play_beep()
            time.sleep(0.2)
            
        messagebox.showinfo("Workout Complete", f"Great job! You completed your workout in {self.format_time(self.total_elapsed)}!")
        
    def play_beep(self):
        try:
            winsound.Beep(800, 300)
        except:
            # Fallback for systems without winsound
            print('\a')
            
    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
            
    def format_time_mm_ss(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
        
    def save_workout(self):
        reps = self.get_reps_data()
        sets = self.sets_var.get()
        
        if not reps:
            messagebox.showwarning("No Reps", "Please add at least one rep.")
            return
            
        name = ctk.CTkInputDialog(text="Enter workout name:", title="Save Workout").get_input()
        if not name:
            return
            
        workout_data = {
            "name": name,
            "sets": sets,
            "reps": reps,
            "created": datetime.now().isoformat()
        }
        
        saved_workouts = self.load_saved_workouts_data()
        saved_workouts[name] = workout_data
        
        with open(self.workouts_file, 'w') as f:
            json.dump(saved_workouts, f, indent=2)
            
        messagebox.showinfo("Success", f"Workout '{name}' saved successfully!")
        
    def load_workout(self):
        saved_workouts = self.load_saved_workouts_data()
        if not saved_workouts:
            messagebox.showinfo("No Workouts", "No saved workouts found.")
            return
            
        # Create selection dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Load Workout")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Select a workout to load:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Workout list
        workout_frame = ctk.CTkScrollableFrame(dialog, height=200)
        workout_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        selected_workout = None
        
        def select_workout(workout_name):
            nonlocal selected_workout
            selected_workout = workout_name
            dialog.destroy()
            
        for name, data in saved_workouts.items():
            workout_btn = ctk.CTkButton(
                workout_frame, 
                text=f"{name} ({data['sets']} sets, {len(data['reps'])} reps)",
                command=lambda n=name: select_workout(n)
            )
            workout_btn.pack(fill="x", pady=2)
            
        dialog.wait_window()
        
        if selected_workout:
            workout_data = saved_workouts[selected_workout]
            
            # Clear existing reps
            for child in self.reps_frame.winfo_children():
                child.destroy()
                
            # Load workout data
            self.sets_var.set(workout_data["sets"])
            
            # Add reps
            for rep_data in workout_data["reps"]:
                self.add_rep()
                children = self.reps_frame.winfo_children()
                last_child = children[-1].winfo_children()
                last_child[1].delete(0, 'end')
                last_child[1].insert(0, rep_data["name"])
                last_child[2].delete(0, 'end')
                last_child[2].insert(0, str(rep_data["duration"]))
                
            messagebox.showinfo("Success", f"Workout '{selected_workout}' loaded successfully!")
            
    def load_saved_workouts_data(self):
        try:
            with open(self.workouts_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def load_saved_workouts(self):
        # This method can be used to populate a dropdown or list if needed
        pass
        
    def load_history(self):
        # Clear existing history
        for child in self.history_frame.winfo_children():
            child.destroy()
            
        try:
            with open(self.history_file, 'r') as f:
                self.workout_history = json.load(f)
        except FileNotFoundError:
            self.workout_history = []
            
        if not self.workout_history:
            ctk.CTkLabel(self.history_frame, text="No workout history yet.").pack(pady=20)
            return
            
        for i, workout in enumerate(reversed(self.workout_history[-10:])):  # Show last 10
            date = datetime.fromisoformat(workout["date"]).strftime("%Y-%m-%d %H:%M")
            
            history_frame = ctk.CTkFrame(self.history_frame)
            history_frame.pack(fill="x", padx=5, pady=2)
            
            info_text = f"{date} - {workout['sets']} sets, {len(workout['reps'])} reps, {self.format_time(workout['total_time'])}"
            ctk.CTkLabel(history_frame, text=info_text, anchor="w").pack(fill="x", padx=10, pady=5)
            
    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.workout_history, f, indent=2)
            
    def export_history(self):
        if not self.workout_history:
            messagebox.showinfo("No History", "No workout history to export.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w') as f:
                f.write("HIIT Me Up - Workout History\n")
                f.write("=" * 40 + "\n\n")
                
                for workout in self.workout_history:
                    date = datetime.fromisoformat(workout["date"]).strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"Date: {date}\n")
                    f.write(f"Sets: {workout['sets']}\n")
                    f.write(f"Total Time: {self.format_time(workout['total_time'])}\n")
                    f.write("Reps:\n")
                    for rep in workout["reps"]:
                        f.write(f"  - {rep['name']}: {rep['duration']}s\n")
                    f.write("\n" + "-" * 40 + "\n\n")
                    
            messagebox.showinfo("Success", f"History exported to {filename}")
            
    def toggle_dark_mode(self):
        self.dark_mode = self.dark_mode_var.get()
        mode = "dark" if self.dark_mode else "light"
        ctk.set_appearance_mode(mode)
        self.save_settings()
        
    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                self.dark_mode = settings.get("dark_mode", True)
                ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        except FileNotFoundError:
            pass
            
    def save_settings(self):
        settings = {
            "dark_mode": self.dark_mode
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        self.is_running = False
        self.save_settings()
        self.root.destroy()

def main():
    try:
        app = HIITTimer()
        app.run()
    except ImportError as e:
        if "customtkinter" in str(e):
            print("CustomTkinter not found. Please install it with:")
            print("pip install customtkinter")
        else:
            print(f"Import error: {e}")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    main()