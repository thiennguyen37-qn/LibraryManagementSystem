from abc import ABC, abstractmethod
from datetime import datetime
class Document(ABC):
  @abstractmethod
  def get_info(self):
    pass
  @abstractmethod
  def __eq__(self,other):
    pass


class Book(Document):

  def __init__(self,title,author,n_pages):
    self.title = title
    self.author = author
    self.n_pages = n_pages

  def get_info(self):
    print(f'Title: {self.title}\nAuthor: {self.author}\nNumber of pages: {self.n_pages}\n')

  def __eq__(self,other):
    return self.title == other.title and self.author == other.author and self.n_pages == other.n_pages


class Magazine(Document):

  def __init__(self,title,issue,n_pages):
    self.title = title
    self.issue = issue
    self.n_pages = n_pages

  def get_info(self):
    print(f'Title: {self.title}\nIssue: {self.issue}\nNumber of pages: {self.n_pages}\n')

  def __eq__(self,other):
    return self.title == other.title and self.issue == other.issue and self.n_pages == other.n_pages


class Exporter(ABC):
  @abstractmethod
  def export_data(self,data):
    pass


class CSVExporter(Exporter):

  def export_data(self,data):
    print(f'Exporting data to CSV: {data}')


class JSONExporter(Exporter):

  def export_data(self,data):
    print(f'Exporting data to JSON: {data}')
class LoggerMixin:

  def log(self,message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f'[{timestamp}] {message}'
    print(log_message)


class User(LoggerMixin):

  def __init__(self,name,id,password,is_admin = False):
    self.name = name
    self.user_id = id
    self.password = password
    self.borrowed_items = []
    self.is_admin = is_admin

  def borrow_item(self,document):
    self.log(f'{self.name} asked for borrowing {document.title}')

  def return_item(self,document):
    self.log(f'{self.name} returned {document.title}')


class LibraryManager(LoggerMixin):

  def __init__(self):
    self.items = [] # Should assign a state of availability for each item instead of removing it
    self.loan_record = []

  def add_item(self,item):
    item_info = dict()
    item_info.update({'document': item})
    item_info.update({'availability': True})
    self.items.append(item_info)
    self.log(f'Added {item.title} to the library')

  def remove_item(self,item):
    self.items = [i for i in self.items if i["document"] != item.title]
    self.log(f'{item.title} was removed from the library')

  def loan_item(self,user,item):
    check = 0
    for i in self.items:
      if (i.get('document') == item):
        check = 1
        if (i.get('availability') == False):
          self.log(f'{item.title} is currently unavailable')
        else:
          record = dict()
          record.update({'loan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
          record.update({'user name': user.name})
          record.update({'user id': user.user_id})
          record.update({'item info': item.title})
          self.loan_record.append(record)
          i['availability'] = False
          user.borrowed_items.append(item)
          self.log(f'The library loaned {item.title} to {user.name} (ID: {user.user_id})')
    if (check == 0):
      self.log(f'The {item.title} does not exist in the library')

  def retake_item(self,user,item):
    user.borrowed_items.remove(item)
    self.log(f'The library retook {item.title} from {user.name} (ID: {user.user_id})')
    for i in self.items:
      if (i.get('document') == item):
        i['availability'] = True
        self.log(f'{item.title} is now available')

  def available_items(self):
    for item in self.items:
      if (item['availability'] == True):
        item.get('document').get_info()

  def export_loan_record(self,exporter):
    exporter.export_data(self.loan_record)