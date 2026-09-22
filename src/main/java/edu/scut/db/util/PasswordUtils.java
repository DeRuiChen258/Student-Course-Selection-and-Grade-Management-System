package edu.scut.db.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.HexFormat;

public final class PasswordUtils {

    private static final SecureRandom RANDOM = new SecureRandom();

    private PasswordUtils() {
    }

    public static String hash(String plain) {
        byte[] salt = new byte[8];
        RANDOM.nextBytes(salt);
        String saltText = HexFormat.of().formatHex(salt);
        return saltText + "$" + sha256(saltText + plain);
    }

    public static boolean verify(String plain, String stored) {
        if (plain == null || stored == null || !stored.contains("$")) {
            return false;
        }
        String[] parts = stored.split("\\$", 2);
        return sha256(parts[0] + plain).equals(parts[1]);
    }

    private static String sha256(String text) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(text.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("当前 JDK 不支持 SHA-256", e);
        }
    }
}
