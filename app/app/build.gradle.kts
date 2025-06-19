plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.example.myapplication"
    compileSdk = 35 // Сделайте compileSdk и targetSdk одинаковыми (или compatible)

    defaultConfig {
        applicationId = "com.example.myapplication"
        minSdk = 31 // Уменьшите minSdk, если это необходимо
        targetSdk = 34 // Сделайте compileSdk и targetSdk одинаковыми (или compatible)
        versionCode = 1
        versionName = "1.0008"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false // В production включите minifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }

    buildFeatures {
        buildConfig = true // Явно включите генерацию BuildConfig
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.constraintlayout)

    // Volley (Если все еще используете)
    implementation(libs.volley)

    // Lifecycle Service
    implementation(libs.androidx.lifecycle.service)

    // Retrofit
    implementation(libs.retrofit)
    implementation(libs.converter.gson)
    implementation(libs.logging.interceptor)

    // RecyclerView
    implementation(libs.androidx.recyclerview)


    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}