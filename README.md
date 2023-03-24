# Crypto

Downloading the git repo locally and creating a virtual environment
*******************************************************************
create a folder where you want to clone the crypto repository or go 
to the local folder where you have all your project directories
cd to this folder and unpack the Crypto project locally
>> cd Repos
>> git clone https://github.com/cryptoroel/Madeira.git

Great, you downloaded the gitup CryptoMadeira project in your local Repos directory

Next step is to set up your virtual_environment

for Linux and Mac OS:
>> cd CryptoMadeira  (goes into the local Crypto directory under Repos/CryptoMadeira)
>> python3.7 -m venv venv 

Activate this virtual environment:
>> source venv/bin/activate

Install all the package from the requirements.txt
>> pip install -r requirements.txt

How to push into the git project:
git push https://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@github.com/cryptoroel/Madeira.git


More useful git commands:
Uploading a complete new repos on github:
-----------------------------------------
1) go to github and press + (upper right corner in https://github.com/cryptoroel
2) go to your local filesystem where your repository is and perform
	-git init
	-git add dirname
	-git commit
	-git remote add origin https://github.com/cryptoroel/reposX.git
	-git push origin master

Creating locally a new branch:
------------------------------
1) git branch feature/Add-trend-plots
2) git checkout feature/Add-trend-plots
3) git add new-python-file
4) git commit * (commits all the files that changed)
5) git push --set-upstream origin feature/Add-trend-plots  (to push in the feature/Add-trend-plots branch on github.com)
6) git branch -d feature/Add-trend-plots  (after the feature/Add-trend-plots is merged in origin/master)
7) git fetch -p  (getting locally the same status of number of branches as github.com)

Since the security has changed one can not push anymore the changes through the pycharm IDE
now you have to do:
git push https://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@github.com/cryptoroel/Crypto.git
git pull https://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@github.com/cryptoroel/Crypto.git