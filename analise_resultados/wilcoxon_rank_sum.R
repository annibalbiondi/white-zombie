sports <- read.csv("esportes.csv", sep=";", header=FALSE)
names(sports) <- c("precision","recall")

economy <- read.csv("economia.csv", sep=";", header=FALSE)
names(economy) <- c("precision", "recall")

aux <- wilcox.test(economy$precision, sports$precision, paired=TRUE, alternative="l")$p.value

res <- aux

aux <- wilcox.test(economy$recall, sports$recall, paired=TRUE, alternative="l")$p.value

res <- cbind(res, aux)

res <- data.frame(res)
names(res) <- c("Precisão","Recall")

print(res)