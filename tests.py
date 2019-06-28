from Remotes import Git


def test_git_clone():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")

def test_build():
    g = Git("https://github.com/adambaumeister/iron-skillet.git")
    g.clone("iron-skillet")
    sc = g.build()
    sk = sc.get_skillet("panorama")
    for s in sk.get_snippets()["snippets"]:
        print(s.get_xpath())

test_build()