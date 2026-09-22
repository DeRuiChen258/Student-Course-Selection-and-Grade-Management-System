package edu.scut.db.tests;

import java.util.LinkedHashMap;
import java.util.Map;

public final class TestRunner {

    @FunctionalInterface
    public interface TestBlock {
        void run() throws Exception;
    }

    private TestRunner() {
    }

    public static void main(String[] args) {
        Map<String, TestBlock> cases = new LinkedHashMap<>();
        cases.put("ValidatorsTest", ValidatorsTest::run);
        cases.put("DaoCrudTest", DaoCrudTest::run);
        cases.put("SqlObjectTest", SqlObjectTest::run);
        cases.put("ServiceFlowTest", ServiceFlowTest::run);
        cases.put("EnrollmentConcurrencyTest", EnrollmentConcurrencyTest::run);
        cases.put("SmokeTest", SmokeTest::run);

        int passed = 0;
        int failed = 0;
        for (Map.Entry<String, TestBlock> entry : cases.entrySet()) {
            long start = System.currentTimeMillis();
            try {
                entry.getValue().run();
                passed++;
                System.out.println("[PASS] " + entry.getKey() + " (" + (System.currentTimeMillis() - start) + " ms)");
            } catch (Throwable e) {
                failed++;
                System.out.println("[FAIL] " + entry.getKey() + " -> " + e.getClass().getSimpleName()
                        + ": " + e.getMessage());
                StackTraceElement[] trace = e.getStackTrace();
                if (trace.length > 0) {
                    System.out.println("       位置 " + trace[0]);
                }
            }
        }
        System.out.println("passed=" + passed + " failed=" + failed);
        if (failed > 0) {
            System.exit(1);
        }
    }
}
