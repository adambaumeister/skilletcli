from Remotes import Git


def test_git_clone():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")

def test_build():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")
    sc = g.build()
    sc.print_all_skillets()

test_build()