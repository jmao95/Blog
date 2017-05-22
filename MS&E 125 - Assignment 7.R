#Assignment 7 - Jonathan Mao


#Problem 1 Part A


poll.data <- read.table("poll_data.tsv", sep="\t", header=TRUE, quote = "\"")
training.data <- read.table("poll_train_small.tsv", sep="\t", header=TRUE, quote = "\"")
test.data <- read.table("poll_test.tsv", sep="\t", header=TRUE, quote = "\"")
complete.training.data <- read.table("poll_train_complete.tsv", sep="\t", header=TRUE, quote = "\"")
model <- glm(vote_2008 == 'barack obama' ~ state + sex + race + age + education + party + ideology + state_contestedness, data=training.data, family = "binomial")
summary(model)

training.data$prediction <- predict(model, type='response')
training.data$vote <- ifelse(training.data$prediction > .5, 'barack obama', 'john mcCain')

#Accuracy calculation
accuracy <- mean(training.data$vote == training.data$vote_2008)
#Accuracy = 0.8925

p <- predict(model, training.data, type = "response")
pred <- prediction(p, training.data$vote_2008=='barack obama')
auc <- performance(pred, "auc")
auc <- unlist(slot(auc, "y.values"))
#AUC = 0.9624


#Problem 1 Part B


test.data$prediction <- predict(model, type='response')
test.data$vote <- ifelse(test.data$prediction > .5, 'barack obama', 'john mcCain')

#Accuracy calculation
accuracy2 <- mean(test.data$vote == test.data$vote_2008)
#Accuracy = 0.4875

p2 <- predict(model, test.data, type = "response")
pred2 <- prediction(p2, test.data$vote_2008=='barack obama')
auc2 <- performance(pred2, "auc")
auc2 <- unlist(slot(auc2, "y.values"))
#AUC = 0.8637


#Problem 1 Part C


model2 <- glm(vote_2008 == 'barack obama' ~ state + sex + race + age + education + party + ideology + state_contestedness, data=complete.training.data, family = "binomial")
summary(model2)

complete.training.data$prediction <- predict(model2, type='response')
complete.training.data$vote <- ifelse(complete.training.data$prediction > .5, 'barack obama', 'john mcCain')

#Performance on new training set

#Accuracy calculation
accuracy3 <- mean(complete.training.data$vote == complete.training.data$vote_2008)
#Accuracy = 0.8561

p3 <- predict(model2, complete.training.data, type = "response")
pred3 <- prediction(p3, complete.training.data$vote_2008=='barack obama')
auc3 <- performance(pred3, "auc")
auc3 <- unlist(slot(auc3, "y.values"))
#AUC = 0.9263

#Performance on test set from 1B

test.data$prediction2 <- predict(model2, newdata=test.data, type='response')
test.data$vote2 <- ifelse(test.data$prediction2 > .5, 'barack obama', 'john mcCain')

#Accuracy calculation
accuracy4 <- mean(test.data$vote2 == test.data$vote_2008)
#Accuracy = 0.8625

p4 <- predict(model2, test.data, type = "response")
pred4 <- prediction(p4, test.data$vote_2008=='barack obama')
auc4 <- performance(pred4, "auc")
auc4 <- unlist(slot(auc4, "y.values"))
#AUC = 0.9095


#Problem 2 Part A

training.data2 <- read.table("poll_train_small.tsv", sep="\t", header=TRUE, quote = "\"")
training.set <- training.data2[1:300,]
validation.set <- training.data2[301:400,]


#Problem 2 Part B

#Calculates AUC for model
test_model <- function(x,y=NULL) {
  if (!is.null(y)) {
    model <- glm(formula = as.formula(paste("vote_2008 == 'barack obama' ~ 1 + ", paste(y, collapse= "+", paste("+ ", x)))), data=training.set, family = "binomial")
  } else {
    model <- glm(formula = as.formula(paste("vote_2008 == 'barack obama' ~ 1 + ", x)), data=training.set, family = "binomial")
  }
  p <- predict(model, validation.set, type = "response")
  pred <- prediction(p, validation.set$vote_2008=='barack obama')
  auc <- performance(pred, "auc")
  auc <- unlist(slot(auc, "y.values"))
  
  return(auc)
}

#AUC for validation set
best.auc = 0
#AUC for training set
best.auc2 = 0
best.model = 0
#voted_2008 removed from feature set
feature.set <- names(training.set)[-8]
#First iteration of forward selection
for(i in feature.set) {
  current.auc = test_model(i)
  if(current.auc > best.auc) {
    best.model = i
    best.auc = current.auc
  }
}
#"party" is best variable


#Problem 2 Part C


#Retrieve AUC for training set
test_model2 <- function(x,y=NULL) {
  if (!is.null(y)) {
    model <- glm(formula = as.formula(paste("vote_2008 == 'barack obama' ~ 1 + ", paste(y, collapse= "+", paste("+ ", x)))), data=training.set, family = "binomial")
  } else {
    model <- glm(formula = as.formula(paste("vote_2008 == 'barack obama' ~ 1 + ", x)), data=training.set, family = "binomial")
  }
  p <- predict(model, training.set, type = "response")
  pred <- prediction(p, training.set$vote_2008=='barack obama')
  auc <- performance(pred, "auc")
  auc <- unlist(slot(auc, "y.values"))
  
  return(auc)
}

#Remove "party" from feature set
feature.set <- feature.set[feature.set != best.model]
#Stores features in order as features are selected in forward selection algorithm
model.features <- c(best.model)
#Stores AUC values for validation set
model.auc <- c(best.auc)
#Stores AUC values for training set
model.auc2 <- c(test_model2("party"))

#Forward selection algorithm stops when it has used all of the features
while(length(feature.set) != 0) {
  #resetting values
  best.auc = 0
  best.model = 0
  #same as in 2B
  for(i in feature.set) {
    current.auc = test_model(i, model.features)
    if(current.auc > best.auc) {
      best.model = i
      best.auc = current.auc
    }
  }
  #Store values before next iteration
  model.features <- append(model.features, best.model)
  model.auc <- append(model.auc, best.auc)
  model.auc2 <- append(model.auc2, test_model2(best.model))
  #Remove feature selected in this iteration
  feature.set <- feature.set[feature.set != best.model]
}

auc_plot <- qplot(factor(model.features, as.character(model.features)), model.auc, xlab="Features", ylab="AUC for validation set")
auc_plot
auc_plot2 <- qplot(factor(model.features, as.character(model.features)), model.auc2, xlab="Features", ylab="AUC for training set")
auc_plot2

#Best model as determined by forward selection
model3 <- glm(vote_2008 == 'barack obama' ~ 1 + party + ideology + race + sex, data=training.data, family = "binomial")
test.data$prediction3 <- predict(model3, newdata=test.data, type='response')
test.data$vote3 <- ifelse(test.data$prediction3 > .5, 'barack obama', 'john mcCain')

#Accuracy calculation
accuracy5 <- mean(test.data$vote3 == test.data$vote_2008)
#Accuracy = 0.8525

p5 <- predict(model3, test.data, type = "response")
pred5 <- prediction(p5, test.data$vote_2008=='barack obama')
auc5 <- performance(pred5, "auc")
auc5 <- unlist(slot(auc5, "y.values"))
#AUC = 0.9079


#Problem 3 Part A

#Clean slate of test data
test.data2 <- read.table("poll_test.tsv", sep="\t", header=TRUE, quote = "\"")

x <- model.matrix(vote_2008 == 'barack obama' ~ ., training.data2)[,-1]
y <- training.data2$vote_2008 == 'barack obama'
model.L1 <- glmnet(x, y, alpha = 1, lambda = 0.01, family="binomial")
model.L2 <- glmnet(x, y, alpha = 0, lambda = 0.01, family="binomial")

x_val <- model.matrix(vote_2008 == 'barack obama' ~ ., test.data2)[,-1]
p6 <- predict(model.L1, newx = x_val, type = "response")
pred6 <- prediction(p6, test.data2$vote_2008=='barack obama')
auc6 <- performance(pred6, "auc")
auc6 <- unlist(slot(auc6, "y.values"))
#L1 AUC = 0.8934

p7 <- predict(model.L2, newx = x_val, type = "response")
pred7 <- prediction(p7, test.data2$vote_2008=='barack obama')
auc7 <- performance(pred7, "auc")
auc7 <- unlist(slot(auc7, "y.values"))
#L2 AUC = 0.8837


#Problem 3 Part B


coef1 <- coef(model.L1)
coef2 <- coef(model.L2)

plot(coef1)
plot(coef2)