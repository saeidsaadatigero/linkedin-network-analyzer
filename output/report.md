# Analysis Report

> Data is synthetic (see README). Findings describe the sample organization only.

## 1. Graph overview

- People (nodes): **10**
- Ties (edges): **19**
- Density: **0.42**
- Connected: **True**

## 2. Key people (centrality)

| Rank | Name | Title | Degree | Betweenness | Influence |
|---|---|---|---|---|---|
| 1 | Daniel Reyes | Head of AI | 0.56 | 0.19 | 1.00 |
| 2 | Mei Tanaka | Product Manager | 0.56 | 0.15 | 0.87 |
| 3 | Lukas Weber | Engineering Manager | 0.44 | 0.12 | 0.69 |
| 4 | Priya Nair | Data Scientist | 0.56 | 0.06 | 0.62 |
| 5 | Elena Markovic | Chief Technology Officer | 0.33 | 0.19 | 0.61 |

- **Daniel Reyes** has the highest combined influence score.
- **Daniel Reyes** has the highest betweenness (0.19): most often on the shortest path between others, i.e. the main bridge.

## 3. Communities (who works closely together)

Greedy modularity found **3** communities (modularity = 0.29).

| Community | Size | Members |
|---|---|---|
| 0 | 4 | Sofia Lindqvist, Daniel Reyes, Priya Nair, Omar Haddad |
| 1 | 3 | James Oconnor, Mei Tanaka, Elena Markovic |
| 2 | 3 | Tomas Silva, Lukas Weber, Anna Kowalski |

## 4. Skill clusters (TF-IDF + KMeans)

Best k = **4** (silhouette = 0.12).

| Cluster | Top skills | Members |
|---|---|---|
| 0 | postgresql, rest api, django, redis, celery | Lukas Weber, Anna Kowalski |
| 1 | machine learning, python, pytorch, mlops, natural language processing | Daniel Reyes, Sofia Lindqvist, Omar Haddad, Priya Nair |
| 2 | roadmapping, user research, hiring, engineering leadership, cloud strategy | Elena Markovic, Mei Tanaka, James Oconnor |
| 3 | terraform, prometheus, linux, kubernetes, ci/cd | Tomas Silva |

## 5. How to read this

- High degree = many direct ties. High betweenness = connects otherwise separate groups.
- A person with high betweenness but modest degree is a hidden broker: losing them would split the network more than their title suggests.
- Communities come from *relationships*, skill clusters from *profile content*. When both agree, teams are well aligned; when they differ, there is cross-functional collaboration.
