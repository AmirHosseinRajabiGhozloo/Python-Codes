# Python-Codes
This repository contains a collection of programming projects implemented in Python. These projects cover different subjects, with a focus on image segmentation and computer vision.

# 1. Rock-Image-Segmentation
This passage discusses the importance of accurately segmenting and identifying pore space and matrix features in core micro-CT images for digital rock physics characterization and analysis. The segmentation of these digital images is crucial for predicting various petrophysical and fluid properties, such as porosity, permeability, and fluid saturation. There are two main categories of methods used for segmenting 2D micro-CT images: traditional thresholding methods and machine learning (ML)-based techniques. Recent studies have shown that ML-based methods, particularly deep learning (DL)-based techniques, outperform traditional thresholding methods due to their advantages, such as lower computational time and cost. The objective of this research is to present an effective hybrid DL technique and compare it with other traditional image segmentation methods. Three DL-based segmentation techniques are utilized: two traditional supervised encoder-decoder structures called U-net and Seg-Net, and a hybrid structure called U-Seg-Net. These techniques are trained, validated, and compared using four different sandstone samples (Parker, Berea, Leopard, and buff Berea sands). The Parker and Leopard datasets are used for training the models, while the other two samples are used as blind datasets for validation. The advantages and disadvantages of each DL-based model are carefully investigated, and the results are compared using several validation parameters, including Intersection-Over-Union (IOU), Jaccard coefficient (JC), Precision, Recall, and F1-score. Despite the differences in the four sandstone datasets, the proposed U-Seg-Net model performs well on all of them. The reported numerical values for IOU, JC, Precision, Recall, and F1-score during the training phase are 80.18, 94.84, 99.56, 99.52, and 99.54, respectively.

# 2. Permeability-Prediction

Prediction of the drilling rate of penetration (ROP) is crucial for maximizing the drilling speed and efficiency. This paper proposes a novel intelligent boosted neural network (called GAN-boosted MLP) to predict the ROP using the petrophysical and drilling parameters. This model is trained through two stepwise stages. In the first stage, the boosting structure (GAN) of the model is created and trained with the target (ROP feature) of the training dataset. This boosting structure enhances the model’s capability to understand the process complexity. In the second stage, the MLP network coupled with the boosting structure is trained with all of the training dataset. The proposed GAN-boosted MLP model provides accurate ROP prediction with both testing and blind datasets. To highlight the superiority of the proposed procedure, a neural network with a similar architecture and without a boosting section, MLP, is also trained and tested. The results show that the proposed GAN-boosted MLP network is more successful in ROP estimation than the original non-boosted network.

# 3. ROP-Prediction

an innovative Deep Learning (DL)-based procedure, named as multiple-input convolutional neural network (MCNN), is developed for estimating reservoir rock permeability. The proposed model fed by two different kinds of input variables, 1D numerical well log data and 2D feature images (generated from available conventional well logs). The model treats and handles each type of data with a compatible network, a 1D-CNN network for the numerical data and a Residual 2D-CNN structure for the image-based dataset. The outputs of two employed DL networks are merged by a concatenated layer. The proposed procedure is implemented on a real dataset form a carbonate reservoir, and qualitative and quantitative analyses of the obtained results reveal its promising accuracy and performance. The MCNN model offers several advantages compared to the conventional single-input networks including the capability of efficiently exploiting mixed data, reducing overfitting problems, and providing more flexibility and accuracy.

# 4. COVID-Detection

This code demonstrates the process of building an image classification model using transfer learning with the InceptionResNet architecture.
It preprocesses the training data, constructs the model, and compiles it for training. 
The code provides a foundation for further training and evaluating the model on the given COVID-19 and Non-COVID-19 image dataset.

# 5. Cancer-Detection

This code segment focuses on cancer image segmentation using the U-Net model.
It preprocesses the cancer-related data, defines the specific architecture for cancer segmentation, provides IOU metrics for evaluating model performance, and sets up the model for training on cancer datasets.

# 6. HyperParameter-Tuning

This code provides a framework for training and optimizing a 2D U-Net model for rock image segmentation.
By leveraging custom loss functions, evaluation metrics, and hyperparameter tuning, the aim is to achieve accurate and precise segmentation of rocks in images, which can have applications in various domains such as geological analysis, environmental monitoring, and resource exploration.
Hyperparameter tuning have been done with Ray Tune. It specifies the search space for the learning rate and sets the stopping criteria.
The tuner fits the model using the defined configuration and returns the best hyperparameters found.

# 7. MNIST

This code demonstrates the construction and training of a neural network model for handwritten digit classification using the MNIST dataset.
By leveraging the TensorFlow and Keras libraries, the code showcases a straightforward implementation of a deep learning model, providing insights into the training progress and performance through visualizations.
