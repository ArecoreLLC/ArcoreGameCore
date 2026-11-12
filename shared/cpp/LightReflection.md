# Light reflection

`LightReflection.h` is an engine-neutral, header-only C++14 specular reflection rule. Input directions and normals are normalized; zero, nonfinite and near-zero vectors are rejected without changing output. Either normal orientation produces the same result. No renderer, collision engine or game state is owned here.

Consumers must supply collision normals, limit bounce count and total distance, offset ray origins after hits, and clear receivers each evaluation. Unreal adapters and puzzle layouts belong to consumers. Vendor and hash-pin the header for standalone builds. Lumen-Weaver is the initial consumer; its Unreal automation exercises reflection, invalid input and physical two-mirror trace/occlusion behavior. Other engines remain unvalidated.
