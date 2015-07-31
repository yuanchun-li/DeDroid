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
        return counter;
    }
}

class SubTestTrain extends TestTrain {
    private double addValue(double base) {
        base += value;
        base += value;
        return base;
    }
}