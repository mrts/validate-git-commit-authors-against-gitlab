# validate-authors.py

Validate Git commit authors against GitLab group members during pushes to Git repository.
See [discussion in Stack Overflow](http://stackoverflow.com/questions/117006/prevent-people-from-pushing-a-git-commit-with-a-different-author-name/)
for context.

Copy `validate-authors.py` to `custom_hooks/pre-receive` in a GitLab server-side Git repository
and make it executable, See [GitLab custom Git hooks docs](http://doc.gitlab.com/ce/hooks/custom_hooks.html)
for detailed installation instructions.

When using with SubGit, do the following:

1. Copy the script to `custom_hooks/validate-authors.py`
2. `chmod 755 custom_hooks/validate-authors.py`
3. Test by running `./custom_hooks/validate-authors.py`
4. Enable it in existing `pre-receive` hook (which already contains SubGit code)
   by adding the following lines to the top before SubGit code:

    # -- START changes for SubGit --
    
    # !!! move this line from below !!!
    HOOK_INPUT=$(cat)
    
    set -e
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    echo "$HOOK_INPUT" | $SCRIPT_DIR/validate-authors.py
    set +e
    
    # -- END changes for SubGit --

