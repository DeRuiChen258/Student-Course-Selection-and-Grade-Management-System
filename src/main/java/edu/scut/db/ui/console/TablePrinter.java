package edu.scut.db.ui.console;

import java.util.List;

public class TablePrinter {

    public void print(String[] headers, List<String[]> rows) {
        if (rows == null || rows.isEmpty()) {
            System.out.println("无匹配记录");
            return;
        }
        int[] widths = new int[headers.length];
        for (int i = 0; i < headers.length; i++) {
            widths[i] = width(headers[i]);
        }
        for (String[] row : rows) {
            for (int i = 0; i < headers.length && i < row.length; i++) {
                widths[i] = Math.max(widths[i], width(row[i]));
            }
        }
        StringBuilder line = new StringBuilder();
        for (int i = 0; i < headers.length; i++) {
            line.append(pad(headers[i], widths[i])).append(i == headers.length - 1 ? "" : " | ");
        }
        System.out.println(line);
        System.out.println("-".repeat(Math.max(10, width(line.toString()))));
        for (String[] row : rows) {
            StringBuilder text = new StringBuilder();
            for (int i = 0; i < headers.length; i++) {
                String cell = i < row.length && row[i] != null ? row[i] : "";
                text.append(pad(cell, widths[i])).append(i == headers.length - 1 ? "" : " | ");
            }
            System.out.println(text);
        }
        System.out.println("共 " + rows.size() + " 行");
    }

    public void printSingle(String[] headers, String[] row) {
        print(headers, java.util.Collections.singletonList(row));
    }

    static int width(String text) {
        if (text == null) {
            return 0;
        }
        int total = 0;
        for (char ch : text.toCharArray()) {
            total += ch > 0x2000 ? 2 : 1;
        }
        return total;
    }

    private static String pad(String text, int width) {
        String value = text == null ? "" : text;
        int padding = width - width(value);
        return value + " ".repeat(Math.max(0, padding));
    }
}
