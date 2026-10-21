"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import {
  ConflictError,
  createCategory,
  deleteCategory,
  deleteProduct,
  getAdminMenu,
  InvalidInputError,
  updateCategory,
  updateProduct,
  createProduct,
  type AdminMenu,
  type AdminProduct,
  type CategoryInput,
  type ProductInput,
} from "@/lib/adminApi";
import type { Key } from "@/lib/i18n";
import { useLang } from "@/lib/useLang";
import { useAdmin } from "../AdminShell";
import styles from "../admin.module.css";
import CategoryForm from "./CategoryForm";
import ProductForm from "./ProductForm";

const PLACEHOLDER = "/menu/placeholder.svg";

type Editing =
  | { kind: "product"; product: AdminProduct | null } // null: new Product
  | { kind: "category"; categoryId: number | null } // null: new Category
  | null;

/** Menu editor: Category chips, the Product table and the forms for both. */
export default function MenuPage() {
  const { t, localized, formatPrice } = useLang();
  const { token, cafe, handleAuthError } = useAdmin();
  const [menu, setMenu] = useState<AdminMenu | null>(null);
  const [selected, setSelected] = useState<number | null>(null); // Category id; null: all
  const [editing, setEditing] = useState<Editing>(null);
  const [error, setError] = useState<Key | null>(null);
  const cafeId = cafe?.id ?? null;

  const load = useCallback(async () => {
    if (cafeId === null) return;
    try {
      setMenu(await getAdminMenu(token, cafeId));
    } catch (e) {
      if (!handleAuthError(e)) setError("admin.error");
    }
  }, [token, cafeId, handleAuthError]);

  useEffect(() => {
    const id = setTimeout(() => {
      setMenu(null);
      setSelected(null);
      setEditing(null);
      setError(null);
      load();
    }, 0);
    return () => clearTimeout(id);
  }, [load]);

  /** Run a change, then reload the Menu. Returns false (and shows why) when it failed. */
  async function change(action: () => Promise<unknown>, conflict: Key = "admin.error"): Promise<boolean> {
    setError(null);
    try {
      await action();
    } catch (e) {
      if (handleAuthError(e)) return false;
      setError(e instanceof ConflictError ? conflict : e instanceof InvalidInputError ? "admin.invalid" : "admin.error");
      return false;
    }
    await load();
    return true;
  }

  if (!cafe) return <p className={styles.empty}>{t("admin.noCafes")}</p>;
  if (!menu) return error ? <p className={styles.error}>{t(error)}</p> : <p className={styles.empty}>{t("common.loading")}</p>;

  const id = cafe.id;
  const category = menu.categories.find((c) => c.id === selected) ?? null;
  const products = category
    ? menu.products.filter((p) => p.category_id === category.id)
    : menu.categories.flatMap((c) => menu.products.filter((p) => p.category_id === c.id)); // in Menu order

  async function saveProduct(input: ProductInput) {
    const product = editing?.kind === "product" ? editing.product : null;
    const ok = await change(() =>
      product ? updateProduct(token, id, product.id, input) : createProduct(token, id, input),
    );
    if (ok) setEditing(null);
  }

  async function removeProduct(product: AdminProduct) {
    if (!confirm(t("admin.confirmDeleteProduct", { name: localized(product.name_ar, product.name_en) }))) return;
    if (await change(() => deleteProduct(token, id, product.id), "admin.productOnOrders")) setEditing(null);
  }

  async function saveCategory(input: CategoryInput) {
    const categoryId = editing?.kind === "category" ? editing.categoryId : null;
    const saved = { id: categoryId };
    const ok = await change(async () => {
      if (categoryId) await updateCategory(token, id, categoryId, input);
      else saved.id = (await createCategory(token, id, input)).id;
    });
    if (!ok) return;
    setEditing(null);
    setSelected(saved.id); // a new Category is picked, ready for its first Product
  }

  async function removeCategory() {
    if (!category || !confirm(t("admin.confirmDeleteCategory", { name: localized(category.name_ar, category.name_en) })))
      return;
    if (await change(() => deleteCategory(token, id, category.id), "admin.categoryHasProducts")) setSelected(null);
  }

  return (
    <>
      <div className={styles.head}>
        <h2 className="serif">{t("admin.menuTitle", { cafe: localized(menu.cafe.name_ar, menu.cafe.name_en) })}</h2>
        <button
          className={styles.btn}
          disabled={menu.categories.length === 0}
          onClick={() => setEditing({ kind: "product", product: null })}
        >
          {t("admin.newProduct")}
        </button>
      </div>

      <div className={styles.chips}>
        <button className={`${styles.chip} ${selected === null ? styles.chipOn : ""}`} onClick={() => setSelected(null)}>
          {t("admin.all")}
        </button>
        {menu.categories.map((c) => (
          <button
            key={c.id}
            className={`${styles.chip} ${selected === c.id ? styles.chipOn : ""}`}
            onClick={() => setSelected(c.id)}
          >
            {localized(c.name_ar, c.name_en)}
          </button>
        ))}
        <button className={`${styles.chip} ${styles.chipAdd}`} onClick={() => setEditing({ kind: "category", categoryId: null })}>
          {t("admin.newCategory")}
        </button>
        {category && (
          <span className={styles.chipActions}>
            <button className={styles.textBtn} onClick={() => setEditing({ kind: "category", categoryId: category.id })}>
              {t("admin.editCategory")}
            </button>
            <button className={`${styles.textBtn} ${styles.danger}`} onClick={removeCategory}>
              {t("admin.deleteCategory")}
            </button>
          </span>
        )}
      </div>

      {error && (
        <p className={styles.error} role="alert">
          {t(error)}
        </p>
      )}

      {editing?.kind === "category" && (
        <CategoryForm
          key={editing.categoryId ?? "new"}
          category={menu.categories.find((c) => c.id === editing.categoryId) ?? null}
          onSave={saveCategory}
          onCancel={() => setEditing(null)}
        />
      )}
      {editing?.kind === "product" && (
        <ProductForm
          key={editing.product?.id ?? "new"}
          product={editing.product}
          categories={menu.categories}
          defaultCategoryId={category?.id ?? menu.categories[0]?.id}
          onSave={saveProduct}
          onDelete={editing.product ? () => removeProduct(editing.product!) : undefined}
          onCancel={() => setEditing(null)}
        />
      )}

      <table className={styles.table}>
        <thead>
          <tr>
            <th aria-label={t("admin.col.image")}></th>
            <th>{t("admin.col.nameAr")}</th>
            <th>{t("admin.col.nameEn")}</th>
            <th>{t("admin.col.price")}</th>
            <th>{t("admin.col.available")}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {products.map((p) => (
            <tr key={p.id}>
              <td>
                <Image className={styles.thumb} src={p.image_url || PLACEHOLDER} alt="" width={36} height={36} unoptimized />
              </td>
              <td>{p.name_ar}</td>
              <td>
                <bdi dir="ltr">{p.name_en || "—"}</bdi>
              </td>
              <td>{formatPrice(p.price)}</td>
              <td>
                <button
                  role="switch"
                  aria-checked={p.available}
                  aria-label={t("admin.availableToggle", { name: localized(p.name_ar, p.name_en) })}
                  className={`${styles.toggle} ${p.available ? "" : styles.toggleOff}`}
                  onClick={() => change(() => updateProduct(token, id, p.id, { available: !p.available }))}
                />
              </td>
              <td>
                <button className={styles.textBtn} onClick={() => setEditing({ kind: "product", product: p })}>
                  {t("admin.edit")}
                </button>
              </td>
            </tr>
          ))}
          {products.length === 0 && (
            <tr>
              <td colSpan={6} className={styles.empty}>
                {t("admin.noProducts")}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}
