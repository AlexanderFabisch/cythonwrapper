import tfd


ok = tfd.tinyfd_message_box("Message Box", "here is my message", "ok", "info", 1)

if ok:
    print("OK")

folder = tfd.tinyfd_select_folder_dialog("Select a folder", ".")
print(folder)
