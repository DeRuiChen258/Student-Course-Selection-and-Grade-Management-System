package edu.scut.db.ui.console;

import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.util.DateUtils;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.Arrays;

public class InputReader {

    private final BufferedReader reader;

    public InputReader() {
        this(System.in);
    }

    public InputReader(InputStream input) {
        this.reader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8));
    }

    public String readLine(String prompt) {
        System.out.print(prompt);
        System.out.flush();
        try {
            String line = reader.readLine();
            return line == null ? "" : line.trim();
        } catch (IOException e) {
            throw new BizException(ErrorCode.E001, "读取输入失败：" + e.getMessage());
        }
    }

    public String readNonEmpty(String prompt) {
        while (true) {
            String value = readLine(prompt);
            if (!value.isEmpty()) {
                return value;
            }
            System.out.println("[E001] 输入不能为空，请重新输入");
        }
    }

    public String readOptional(String prompt) {
        return readLine(prompt);
    }

    public int readInt(String prompt, int min, int max) {
        while (true) {
            String value = readLine(prompt);
            try {
                int number = Integer.parseInt(value);
                if (number < min || number > max) {
                    System.out.println("[E001] 请输入 " + min + " 到 " + max + " 之间的整数");
                    continue;
                }
                return number;
            } catch (NumberFormatException e) {
                System.out.println("[E001] 不是合法整数，请重新输入");
            }
        }
    }

    public Integer readOptionalInt(String prompt, int min, int max) {
        while (true) {
            String value = readLine(prompt);
            if (value.isEmpty()) {
                return null;
            }
            try {
                int number = Integer.parseInt(value);
                if (number < min || number > max) {
                    System.out.println("[E001] 请输入 " + min + " 到 " + max + " 之间的整数");
                    continue;
                }
                return number;
            } catch (NumberFormatException e) {
                System.out.println("[E001] 不是合法整数，请重新输入");
            }
        }
    }

    public BigDecimal readDecimal(String prompt, BigDecimal min, BigDecimal max) {
        while (true) {
            String value = readLine(prompt);
            try {
                BigDecimal number = new BigDecimal(value);
                if (number.compareTo(min) < 0 || number.compareTo(max) > 0) {
                    System.out.println("[E001] 请输入 " + min + " 到 " + max + " 之间的数值");
                    continue;
                }
                return number;
            } catch (NumberFormatException e) {
                System.out.println("[E001] 不是合法数值，请重新输入");
            }
        }
    }

    public LocalDate readDate(String prompt, boolean optional) {
        while (true) {
            String value = readLine(prompt);
            if (value.isEmpty() && optional) {
                return null;
            }
            LocalDate date = DateUtils.parseDate(value);
            if (date != null) {
                return date;
            }
            System.out.println("[E001] 日期格式应为 yyyy-MM-dd，请重新输入");
        }
    }

    public String readEnum(String prompt, String... options) {
        while (true) {
            String value = readLine(prompt + Arrays.toString(options) + ": ");
            for (String option : options) {
                if (option.equals(value)) {
                    return value;
                }
            }
            System.out.println("[E001] 只能输入 " + String.join("/", options));
        }
    }

    public boolean readConfirm(String prompt) {
        String value = readLine(prompt + "（y/N）: ");
        return value.equalsIgnoreCase("y") || value.equalsIgnoreCase("yes");
    }
}
