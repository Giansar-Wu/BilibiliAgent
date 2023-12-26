import gui

def main():
    app = gui.QApplication()
    win = gui.MyMainWindow()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()