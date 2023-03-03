from browser.model import Model, Item
from browser.window import App

model = Model()
model.load_from_saved_sources()

App(model).start()