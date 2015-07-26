package com.lynnlyc.sootextension;

/**
 * Created by LiYC on 2015/7/25.
 * Package: com.lynnlyc.sootextension
 * PackageSeg represent a segment of a package name
 * e.g. in package name com.lynnlyc.sootextension, we have three PackageSegs:
 * com, lynnlyc, and sootextension
 * Why don't use a String?
 * Because the 'a' in com.alice.a and com.bob.a are equal as Strings,
 * but not equal as PackageSegs
 */
public class PackageSeg {
    private String packageName;
    private String segName;

    public PackageSeg(String packageName,String segName) {
        assert packageName.endsWith(segName);
        this.packageName = packageName;
        this.segName = segName;
    }

    @Override
    public boolean equals(Object obj) {
        if (!(obj instanceof PackageSeg))
            return false;
        PackageSeg other = (PackageSeg) obj;
        return this.packageName.equals(other.packageName)
                && this.segName.equals(other.segName);
    }

    public String getSegName() {
        return this.segName;
    }

    public void setSegName(String segName) {
        this.segName = segName;
    }
}
