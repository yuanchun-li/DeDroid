package com.example;

class ExampleActivity extends Activity {
    public static String helloMessage;
    private TextView helloTextView;

    protected void onCreate(Bundle ...) {
        helloTextView = this.findViewById(...);
        helloMessage = Util.getMessage();
        helloTextView.setText(helloMessage);
        ...
    }
}

class Util {
    public static String getMessage() {
        return "...";
    }
}
