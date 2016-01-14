package testpackage;

class TestTrain {
    protected double value = 1.0;
    public int counter = 3;
    private double addValue(double base) {
        base += value;
        counter = counterIncrease();
        return base;
    }
    public int counterIncrease() {
        counter += 1;
        func2(0.1, counter);
        return counter;
    }

    public void func2(double a, int b) {
        int c = b + (int)a;
    }

    public int func3(int a) {
        int b = func3(a);
        value = b;
        return b;
    }
}

class SubTestTrain extends TestTrain {
    private double addValue(double base) {
        base += value;
        base += value;
        return base;
    }

    public void func2(double a, int b) {
        int c = b - (int)a;
    }
}