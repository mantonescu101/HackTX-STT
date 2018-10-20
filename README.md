###Workflow
<pre>
  Update local repo
    - git checkout master
    - git pull origin master
  Create working branch
    - git checkout -b WORKING_BRANCH
  Make changes on WORKING_BRANCH
  Add and commit changes once satisfied
    - git add /files/you/changed
    - git commit -m "Message describing changes"
  Push changes to master
    - git checkout master
    - git pull origin master
    - git merge WORKING_BRANCH
    - git push origin master
</pre>
