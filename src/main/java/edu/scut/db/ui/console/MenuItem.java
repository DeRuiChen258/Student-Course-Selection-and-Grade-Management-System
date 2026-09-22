package edu.scut.db.ui.console;

import java.util.ArrayList;
import java.util.List;

public class MenuItem {

    private final String title;
    private final Action action;
    private final List<MenuItem> children = new ArrayList<>();

    public MenuItem(String title, Action action) {
        this.title = title;
        this.action = action;
    }

    public static MenuItem group(String title) {
        return new MenuItem(title, null);
    }

    public MenuItem add(MenuItem child) {
        children.add(child);
        return this;
    }

    public String getTitle() {
        return title;
    }

    public Action getAction() {
        return action;
    }

    public List<MenuItem> getChildren() {
        return children;
    }

    public boolean isGroup() {
        return !children.isEmpty();
    }
}
