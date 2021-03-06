# -*- coding: utf-8 -*-
"""transfer_learning_debug.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1A72O596HRhS-ZO973Skuz3BeIs5sVkEU
"""

# data transform
from torchvision import transforms
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
}

!apt-get install -y -qq software-properties-common python-software-properties module-init-tools
!add-apt-repository -y ppa:alessandro-strada/ppa 2>&1 > /dev/null
!apt-get update -qq 2>&1 > /dev/null
!apt-get -y install -qq google-drive-ocamlfuse fuse
from google.colab import auth
auth.authenticate_user()
from oauth2client.client import GoogleCredentials
creds = GoogleCredentials.get_application_default()
import getpass
!google-drive-ocamlfuse -headless -id={creds.client_id} -secret={creds.client_secret} < /dev/null 2>&1 | grep URL
vcode = getpass.getpass()
!echo {vcode} | google-drive-ocamlfuse -headless -id={creds.client_id} -secret={creds.client_secret}

!mkdir -p drive
!google-drive-ocamlfuse drive

!ls /content/drive/trans_learn/datasets



# creating datasets 
import os
from torchvision import datasets
data_dir = '/content/drive/trans_learn/datasets'
image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'val']}
# print(image_datasets)

# creating dataloader
import torch
dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x],
                                             batch_size = 4,
                                             shuffle = True) for x in ['train', 'val']}
# print(dataloaders)
# dictionary to collect the length of each datasets
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
# print(dataset_sizes)

# creating class name
class_names = image_datasets['train'].classes

# printing values
print('class names: {}'.format(class_names))
print('there are {} batches in training datasets'.format(len(dataloaders['train'])))
print('there are {} batches in the validation/testing datasets'.format(len(dataloaders['val'])))
print('there are {} images in the training datasets'.format(len(image_datasets['train'])))
print('there are {} images in the testing/validating datasets'.format(len(image_datasets['val'])))

# loading the model
from torchvision import models
model = models.resnet18(pretrained = True)

# freeze all the layers of resnet18
for param in model.parameters():
    param.requires_grad = False

# get the number of inputs in the last layer(or number of neurons in the layer preceeding the last layer)
num_ftrs = model.fc.in_features
num_ftrs

# reconstruct the last layer
import torch.nn as nn
model.fc = nn.Linear(num_ftrs, 2)

# switching netween CPU and GPU
cuda = torch.cuda.is_available()
if cuda:
    model = model.cuda()

# understand what's happening
from torch.autograd import Variable
iteration = 0
correct = 0
for inputs, labels in dataloaders['train']:
    if iteration == 1:
        break
    inputs = Variable(inputs)
    labels = Variable(labels)
    if cuda:
        inputs = inputs.cuda()
        labels = labels.cuda()
    output = model(inputs)
    _, predicted = torch.max(output, 1)
    if cuda:
        correct += (predicted.cpu() == labels.cpu()).sum()
    else:
        correct += (predicted == labels).sum()
    print('for one iteration this is what happens:')
    print('input shape: ', inputs.shape)
    print('label shape: ', labels.shape)
    print('label are: {}'.format(labels))
    print('output tensor: ', output)
    print("output's shape: ", output.shape)
    print('predicted: ', predicted)
    print("predicted's shape: ", predicted.shape)
    print('correct predictions: ', correct)
    iteration += 1

# defining loss function
loss_function = nn.CrossEntropyLoss()
# define optimization function
import torch.optim as optim
optimizer = optim.SGD(model.fc.parameters(), lr = 0.001, momentum = 0.9)
# define learning rate scheduler
from torch.optim import lr_scheduler
exp_lr_scheduler = lr_scheduler.StepLR(optimizer, step_size = 7, gamma = 0.1)

# training the network
num_epochs = 30
for epoch in range(num_epochs):
  correct = 0
  exp_lr_scheduler.step()
  for images, labels in dataloaders['train']:
    images = Variable(images)
    labels = Variable(labels)
    if cuda:
      images = images.cuda()
      labels = labels.cuda()
    optimizer.zero_grad()
    output = model(images)
    loss = loss_function(output, labels)
    loss.backward()
    optimizer.step()
    _, predicted = torch.max(output, 1)
    if cuda:
      correct += (predicted.cpu() == labels.cpu()).sum()
    else:
      correct += (predicted == labels).sum()
      
  training_acc = 100 * correct / dataset_sizes['train']
  
  print('Epoch [{}/{}] loss: {:.4f} training accuracy: {}%'.format(epoch + 1, num_epochs, loss.item(), training_acc))

# testing the model
model.eval()
with torch.no_grad():
  correct = 0
  for images, labels in dataloaders['val']:
    images = Variable(images)
    labels = Variable(labels)
    if cuda:
      images = images.cuda()
      labels = labels.cuda()
    output = model(images)
    loss = loss_function(output, labels)
    _, prediction = torch.max(output, 1)
    if cuda:
      correct += (prediction.cpu() == labels.cpu()).sum()
    else:
      correct += (prediction == labels).sum()
  testing_acc = 100 * correct / dataset_sizes['val']
  print('testing accuracy: {}%'.format(testing_acc))

# visualizing some prediction
import matplotlib.pyplot as plt
import numpy as np
fig = plt.figure()
shown_batch = 0
index = 0
with torch.no_grad():
  for images, labels in dataloaders['val']:
    if shown_batch == 1:
      break
    images = Variable(images)
    labels = Variable(labels)
    if cuda:
      images = images.cuda()
      labels = labels.cuda()
    output = model(images)
    _, prediction = torch.max(output, 1)
    
    for i in range(4):
      index += 1
      ax = plt.subplot(2, 2, index)
      ax.axis('off')
      ax.set_title('predicted label: {}'.format(class_names[prediction[i]]))
      input_image = images.cpu().data[i]
      inp = input_image.numpy().transpose((1, 2, 0))
      mean = [0.485, 0.456, 0.406]
      std = [0.229, 0.224, 0.225]
      inp = std * inp + mean
      inp = np.clip(inp, 0, 1)
      plt.imshow(inp)
    shown_batch += 1

detect_transform = transforms.Compose([transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
# detecting an image
import matplotlib.image as mpimage
import cv2
from PIL import Image
def detect(image, model):
  image = cv2.imread(image)
  image = Image.fromarray(image)
  image = detect_transform(image)
  image = image.view(1, 3, 224, 224)
  image = Variable(image)
  model.eval()
  if cuda:
    model = model.cuda()
    image = image.cuda()
  output = model(image)
  _, predicted = torch.max(output, 1)
  return predicted.item()
prediction = detect('/content/drive/trans_learn/testing/test2.jpg', model)
print('detected output is: {}'.format(class_names[prediction]))

img = cv2.imread('/content/drive/trans_learn/testing/test2.jpg')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = Image.fromarray(img)
plt.imshow(img)



