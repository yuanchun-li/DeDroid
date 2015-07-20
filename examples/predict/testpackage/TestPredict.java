package testpackage;

class TestPredict {
    protected double value = 1.0;
    public int counter = 3;
    private double addValue(double base) {
        base += value;
        counterIncrease();
        return base;
    }
    public int counterIncrease() {
        counter += 1;
        return counter;
    }
}

class SubTestPredict extends TestPredict {
    private double addValue(double base) {
        base += value;
        base += value;
        return base;
    }
}